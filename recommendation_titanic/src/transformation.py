from sqlalchemy import create_engine, text

from config import DATABASE_URL, TARGET_SCHEMA
from database_io import upsert_dataframe


def build_features(users, products, interactions):
    data = interactions.merge(users, on="user_id", how="left")
    data = data.merge(products[["product_id", "category", "price", "popularity_score"]], on="product_id", how="left")

    user_features = data.groupby("user_id").agg(
        user_activity_count=("product_id", "count"),
        average_rating_per_user=("rating", "mean"),
    ).reset_index()

    item_features = data.groupby("product_id").agg(
        item_rating_count=("rating", "count"),
        average_rating_per_item=("rating", "mean"),
    ).reset_index()

    interaction_features = data.merge(user_features, on="user_id", how="left")
    interaction_features = interaction_features.merge(item_features, on="product_id", how="left")

    interaction_features["rating_normalized"] = (
        (interaction_features["rating"] - 1.0) / 4.0
    ).round(6)

    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{TARGET_SCHEMA}"'))

    upsert_dataframe(engine, interaction_features, TARGET_SCHEMA, "recommendation_features", ["user_id", "product_id"])
    upsert_dataframe(engine, user_features, TARGET_SCHEMA, "user_features", ["user_id"])
    upsert_dataframe(engine, item_features, TARGET_SCHEMA, "item_features", ["product_id"])

    return interaction_features, user_features, item_features
