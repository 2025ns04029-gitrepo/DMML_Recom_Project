import logging

from prefect import flow, task

from config import LOG_DIR
from ingestion import ingest_to_postgres
from validation import validate_data
from transformation import build_features
from feature_store import initialize_feature_registry, retrieve_features
from model_training import train_model

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_DIR / "pipeline.log")],
)


@task(retries=2, retry_delay_seconds=5)
def ingestion_task():
    return ingest_to_postgres()


@task
def validation_task(users, products, interactions):
    valid, issues, report = validate_data(users, products, interactions)
    if not valid:
        raise ValueError("Data validation failed: " + "; ".join(issues))
    logging.info("Data quality report:\n%s", report.to_string(index=False))
    return report


@task
def transformation_task(users, products, interactions):
    return build_features(users, products, interactions)


@task
def feature_store_task():
    initialize_feature_registry()
    return retrieve_features("user")


@task
def training_task(interactions):
    return train_model(interactions)


@flow(name="Titanic Data Management Pipeline")
def titanic_pipeline():
    users, products, interactions = ingestion_task()
    validation_task(users, products, interactions)
    interaction_features, user_features, item_features = transformation_task(users, products, interactions)
    registry = feature_store_task()
    metadata, recommendations = training_task(interactions)
    logging.info("Feature registry entries: %s", registry)
    logging.info("Model metadata: %s", metadata)
    return metadata


if __name__ == "__main__":
    titanic_pipeline()
