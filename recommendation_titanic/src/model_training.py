import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
from sklearn.neighbors import NearestNeighbors

try:
    from .config import MODEL_DIR
except ImportError:
    from config import MODEL_DIR


def precision_recall_at_k(recommendations, relevant, k=10):
    precisions = []
    recalls = []
    for user_id, rec_ids in recommendations.items():
        truth = relevant.get(user_id, set())
        hits = len(set(rec_ids[:k]) & truth)
        precisions.append(hits / k)
        recalls.append(hits / len(truth) if truth else 0)
    return float(np.mean(precisions)), float(np.mean(recalls))


def train_model(interactions, k=20):
    # Hold out 20% of each user's interactions so evaluation does not train on test items.
    interactions = interactions.copy().sort_values(["user_id", "product_id"])
    train_parts = []
    test_parts = []
    for _, user_interactions in interactions.groupby("user_id", sort=False):
        split_index = max(1, int(len(user_interactions) * 0.8))
        train_parts.append(user_interactions.iloc[:split_index])
        test_parts.append(user_interactions.iloc[split_index:])

    train = pd.concat(train_parts, ignore_index=True)
    test = pd.concat(test_parts, ignore_index=True)
    matrix = train.pivot_table(index="user_id", columns="product_id", values="rating", aggfunc="mean").fillna(0)

    neighbor_count = min(k, max(1, len(matrix)))
    neighbor_count = min(neighbor_count + 1, len(matrix))
    neighbors = NearestNeighbors(
        n_neighbors=neighbor_count,
        metric="cosine",
    )
    neighbors.fit(matrix)
    _, neighbor_indices = neighbors.kneighbors(matrix)

    reconstructed = np.zeros(matrix.shape, dtype=float)
    for row_index, indices in enumerate(neighbor_indices):
        other_indices = indices[indices != row_index]
        if len(other_indices) == 0:
            reconstructed[row_index] = matrix.iloc[row_index].to_numpy()
            continue

        distances, selected_indices = neighbors.kneighbors(
            matrix.iloc[[row_index]],
            n_neighbors=len(other_indices) + 1,
        )
        selected_indices = selected_indices[0]
        selected_indices = selected_indices[selected_indices != row_index]
        distances = distances[0][:len(selected_indices)]
        weights = 1.0 / (distances + 1e-8)
        neighbor_ratings = matrix.iloc[selected_indices].to_numpy()
        reconstructed[row_index] = np.average(
            neighbor_ratings,
            axis=0,
            weights=weights,
        )

    reconstructed = np.clip(reconstructed, 1, 5)

    test_predictions = []
    test_actuals = []
    recommendations = {}
    relevant = {}

    for user_id in test["user_id"].unique():
        user_test = test.loc[test["user_id"] == user_id]
        relevant[user_id] = set(user_test["product_id"])

        if user_id not in matrix.index:
            continue

        row_index = matrix.index.get_loc(user_id)
        scores = reconstructed[row_index]
        seen = set(train.loc[train["user_id"] == user_id, "product_id"])

        ranked = [
            product_id
            for product_id, score in sorted(
                zip(matrix.columns, scores),
                key=lambda item: item[1],
                reverse=True,
            )
            if product_id not in seen
        ]
        recommendations[user_id] = ranked

        for _, row in user_test.iterrows():
            if row["product_id"] in matrix.columns:
                product_index = matrix.columns.get_loc(row["product_id"])
                test_predictions.append(reconstructed[row_index, product_index])
                test_actuals.append(row["rating"])

    rmse = float(np.sqrt(mean_squared_error(test_actuals, test_predictions))) if test_predictions else 0.0
    precision, recall = precision_recall_at_k(recommendations, relevant, k=10)

    metadata = {
        "model_type": "NearestNeighbors",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "neighbor_count": min(k, max(1, len(matrix) - 1)),
        "distance_metric": "cosine",
        "rmse": round(rmse, 4),
        "precision_at_10": round(precision, 4),
        "recall_at_10": round(recall, 4),
        "users": matrix.shape[0],
        "products": matrix.shape[1],
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    np.save(MODEL_DIR / "reconstruction.npy", reconstructed)
    pd.DataFrame({"user_id": matrix.index}).to_csv(MODEL_DIR / "matrix_users.csv", index=False)
    pd.DataFrame({"product_id": matrix.columns}).to_csv(MODEL_DIR / "matrix_products.csv", index=False)
    with open(MODEL_DIR / "metadata.json", "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    return metadata, recommendations
