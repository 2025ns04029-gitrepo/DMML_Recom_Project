# Data Versioning and Lineage

Each ingestion batch is stored in:

```text
data/raw/YYYYMMDDTHHMMSSZ/
```

Each batch contains:

- `users.csv`
- `products.csv`
- `interactions.csv`

The batch timestamp is also stored in ingestion metadata and event timestamps. Recommended Git/DVC workflow:

```bash
dvc init
dvc add recommendation_titanic/data/raw recommendation_titanic/data/processed
git add .dvc .gitignore recommendation_titanic
git commit -m "Version Recommendation Titanic datasets"
```

Lineage:

```text
Users/Products/Interactions CSV
  -> schema_1 raw PostgreSQL tables
  -> validation report
  -> schema_2 recommendation_features/user_features/item_features
  -> feature_store.db
  -> Truncated SVD model
  -> models/metadata.json
```

## PostgreSQL load strategy

- **Users:** upserted on `user_id`
- **Products:** upserted on `product_id`; category and price changes update existing rows
- **Interactions:** appended as event history
- **Recommendation features:** upserted for current user-product feature snapshots
