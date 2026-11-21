from datetime import datetime, timezone
import logging
import uuid

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

try:
    from .config import DATABASE_URL, SOURCE_SCHEMA, RAW_DIR, LOG_DIR
    from .database_io import append_dataframe, upsert_dataframe
except ImportError:
    from config import DATABASE_URL, SOURCE_SCHEMA, RAW_DIR, LOG_DIR
    from database_io import append_dataframe, upsert_dataframe

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_DIR / "pipeline.log")],
)
log = logging.getLogger(__name__)


def generate_demo_data(seed=42, users=300, products=100, category_overrides=None):
    rng = np.random.default_rng(seed)
    ingest_time = datetime.now(timezone.utc).isoformat()

    product_categories = rng.choice(["Electronics", "Books", "Fashion", "Home", "Sports"], products)
    products_df = pd.DataFrame({
        "product_id": range(1, products + 1),
        "category": product_categories,
        "price": np.round(rng.lognormal(mean=3.5, sigma=0.7, size=products), 2),
        "popularity_score": rng.uniform(0, 1, products).round(4),
        "ingested_at": ingest_time,
    })

    if category_overrides:
        for product_id, category in category_overrides.items():
            products_df.loc[products_df["product_id"] == int(product_id), "category"] = category

    users_df = pd.DataFrame({
        "user_id": range(1, users + 1),
        "age_group": rng.choice(["18-24", "25-34", "35-44", "45-54", "55+"], users),
        "region": rng.choice(["North", "South", "East", "West"], users),
        "ingested_at": ingest_time,
    })

    interactions = []
    for user_id in range(1, users + 1):
        purchase_count = min(int(rng.integers(5, 25)), products)
        purchased = rng.choice(
            products_df["product_id"],
            size=purchase_count,
            replace=False,
        )
        for product_id in purchased:
            interactions.append((
                user_id,
                int(product_id),
                int(rng.integers(1, 6)),
                "selected",
                ingest_time,
                str(uuid.uuid4())
            ))

    interactions_df = pd.DataFrame(interactions, columns=[
        "user_id", "product_id", "rating", "event_type", "event_timestamp", "uuid"
    ])
    return users_df, products_df, interactions_df


def ingest_to_postgres(batch_id=None, category_overrides=None):
    batch_id = batch_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    batch_dir = RAW_DIR / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)

    users, products, interactions = generate_demo_data(category_overrides=category_overrides)
    users.to_csv(batch_dir / "users.csv", index=False)
    products.to_csv(batch_dir / "products.csv", index=False)
    interactions.to_csv(batch_dir / "interactions.csv", index=False)

    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{SOURCE_SCHEMA}"'))

    upsert_dataframe(engine, users, SOURCE_SCHEMA, "users", ["user_id"])
    upsert_dataframe(engine, products, SOURCE_SCHEMA, "products", ["product_id"])
    append_dataframe(
        engine,
        interactions,
        SOURCE_SCHEMA,
        "interactions",
        primary_keys=["user_id", "product_id"],
    )

    # Reload all interactions from PostgreSQL to ensure we have the latest data
    interactions = pd.read_sql_table("interactions", engine, schema=SOURCE_SCHEMA)

    log.info("Ingested batch %s: %d users, %d products, %d interactions",
             batch_id, len(users), len(products), len(interactions))
    return users, products, interactions


if __name__ == "__main__":
    ingest_to_postgres()
