import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_NAME = os.getenv("RECOMMENDATION_TITANIC_DB", "titanic")
DB_USER = os.getenv("RECOMMENDATION_TITANIC_DB_USER", "shubhangi")
DB_PASSWORD = os.getenv("RECOMMENDATION_TITANIC_DB_PASSWORD")
DB_HOST = os.getenv("RECOMMENDATION_TITANIC_DB_HOST", "localhost")
DB_PORT = os.getenv("RECOMMENDATION_TITANIC_DB_PORT", "5432")
if DB_PASSWORD:
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    DATABASE_URL = f"postgresql+psycopg2://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SOURCE_SCHEMA = "schema_1"
TARGET_SCHEMA = "schema_2"
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODEL_DIR = BASE_DIR / "models"
LOG_DIR = BASE_DIR / "logs"
