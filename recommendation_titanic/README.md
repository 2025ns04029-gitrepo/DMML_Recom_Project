# Recommendation Titanic End-to-End Data Management Pipeline

This project implements a reproducible recommendation pipeline using PostgreSQL schemas:

- `schema_1`: raw users, products, and interactions
- `schema_2`: transformed recommendation, user, and item features

## PostgreSQL load modes

- `users`: upsert on `user_id`
- `products`: upsert on `product_id`; category, price, and popularity updates are applied to existing products
- `interactions`: append-only event history
- `schema_2` tables: rebuilt for a current feature snapshot

## Project structure

```text
recommendation_titanic/
├── data/raw/                 Timestamped ingestion batches
├── data/processed/           Processed outputs
├── logs/                     Pipeline logs
├── models/                   Model artifacts and metadata
├── src/                      Modular pipeline source code
├── tests/                    Validation unit tests
├── requirements.txt
├── README.md
└── titanic_md_file.md
```

## Setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ensure PostgreSQL is running and the `titanic` database exists. The default connection in `src/config.py` uses:

```text
postgresql+psycopg2://shubhangi@localhost:5432/titanic
```

## Run the pipeline

```bash
cd recommendation_titanic
python src/pipeline.py
```

## Run tests

```bash
pytest -q
```

## Pipeline components

1. Ingestion generates and stores synthetic Recommendation Titanic data.
2. Validation checks ranges, nulls, duplicates, and foreign-key references.
3. Transformation creates user, item, and interaction features.
4. The feature store registry documents feature definitions and versions.
5. Truncated SVD trains a collaborative-filtering model.
6. Prefect orchestrates tasks and logs execution.

## Evaluation

The model reports:

- RMSE
- Precision@10
- Recall@10

Replace the synthetic source with real transaction/API data before production deployment.
