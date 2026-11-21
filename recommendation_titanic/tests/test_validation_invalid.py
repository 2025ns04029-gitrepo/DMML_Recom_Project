import pandas as pd
from src.validation import validate_data


def test_validation_rejects_out_of_range_rating():
    users = pd.DataFrame({"user_id": [1]})
    products = pd.DataFrame({"product_id": [10]})
    interactions = pd.DataFrame({
        "user_id": [1],
        "product_id": [10],
        "rating": [9],
    })

    valid, issues, report = validate_data(users, products, interactions)

    assert not valid
    assert any("range 1-5" in issue for issue in issues)
