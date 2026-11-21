import json

import pandas as pd

from src.model_training import train_model


def test_train_model_uses_nearest_neighbors(tmp_path, monkeypatch):
    interactions = pd.DataFrame({
        "user_id": [1, 1, 1, 2, 2, 2, 3, 3, 3],
        "product_id": [10, 20, 30, 10, 20, 40, 10, 30, 40],
        "rating": [5, 4, 3, 5, 5, 2, 4, 4, 3],
    })

    monkeypatch.setattr("src.model_training.MODEL_DIR", tmp_path)

    metadata, recommendations = train_model(interactions, k=2)

    assert metadata["model_type"] == "NearestNeighbors"
    assert metadata["distance_metric"] == "cosine"
    assert recommendations
    assert (tmp_path / "reconstruction.npy").exists()
    assert (tmp_path / "matrix_users.csv").exists()
    assert (tmp_path / "matrix_products.csv").exists()
    assert json.loads((tmp_path / "metadata.json").read_text())["model_type"] == "NearestNeighbors"
