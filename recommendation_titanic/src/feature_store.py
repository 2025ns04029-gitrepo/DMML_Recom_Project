import sqlite3
from pathlib import Path

FEATURE_STORE_DB = Path(__file__).resolve().parents[1] / "feature_store.db"


def initialize_feature_registry():
    with sqlite3.connect(FEATURE_STORE_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feature_registry (
                feature_name TEXT PRIMARY KEY,
                source_tables TEXT NOT NULL,
                transformation TEXT NOT NULL,
                version TEXT NOT NULL,
                entity TEXT NOT NULL
            )
        """)
        rows = [
            ("user_activity_count", "interactions", "count(product_id) by user_id", "v1", "user"),
            ("average_rating_per_user", "interactions", "mean(rating) by user_id", "v1", "user"),
            ("item_rating_count", "interactions", "count(rating) by product_id", "v1", "item"),
            ("average_rating_per_item", "interactions", "mean(rating) by product_id", "v1", "item"),
            ("rating_normalized", "interactions", "(rating - 1) / 4", "v1", "interaction"),
        ]
        conn.executemany("INSERT OR REPLACE INTO feature_registry VALUES (?, ?, ?, ?, ?)", rows)


def retrieve_features(entity="user"):
    with sqlite3.connect(FEATURE_STORE_DB) as conn:
        cursor = conn.execute(
            "SELECT feature_name, source_tables, transformation, version FROM feature_registry WHERE entity = ?",
            (entity,),
        )
        return cursor.fetchall()
