import pandas as pd
from src.validation import validate_data
from src.ingestion import generate_demo_data


def test_generated_interactions_include_uuid():
    _, _, interactions = generate_demo_data(users=2, products=5)

    assert "uuid" in interactions.columns
    assert interactions["uuid"].str.match(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    ).all()


def test_validation_accepts_valid_data():
    users = pd.DataFrame({"user_id": [1, 2]})
    products = pd.DataFrame({"product_id": [10, 20]})
    interactions = pd.DataFrame({
        "user_id": [1, 2],
        "product_id": [10, 20],
        "rating": [4, 5],
    })

    valid, issues, report = validate_data(users, products, interactions)

    assert valid
    assert issues == []
    assert len(report) == 6


def test_validation_rejects_duplicate_user_product_pairs():
    users = pd.DataFrame({"user_id": [1]})
    products = pd.DataFrame({"product_id": [10]})
    interactions = pd.DataFrame({
        "user_id": [1, 1],
        "product_id": [10, 10],
        "rating": [4, 5],
    })

    valid, issues, report = validate_data(users, products, interactions)

    assert not valid
    assert any("duplicate user-product interactions" in issue for issue in issues)
