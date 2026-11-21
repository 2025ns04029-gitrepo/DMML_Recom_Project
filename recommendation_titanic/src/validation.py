import pandas as pd


def validate_data(users, products, interactions):
    issues = []

    if users["user_id"].duplicated().any():
        issues.append("Duplicate user_id values")
    if products["product_id"].duplicated().any():
        issues.append("Duplicate product_id values")
    if interactions["user_id"].isna().any() or interactions["product_id"].isna().any():
        issues.append("Missing user or product identifiers")

    invalid_ratings = interactions.loc[
        ~interactions["rating"].between(1, 5)
    ]
    if not invalid_ratings.empty:
        issues.append(f"{len(invalid_ratings)} ratings outside range 1-5")

    duplicate_pairs = interactions.duplicated(["user_id", "product_id"])
    if duplicate_pairs.any():
        issues.append(f"{duplicate_pairs.sum()} duplicate user-product interactions")

    unknown_users = set(interactions["user_id"]) - set(users["user_id"])
    unknown_products = set(interactions["product_id"]) - set(products["product_id"])
    if unknown_users:
        issues.append(f"Unknown user IDs: {len(unknown_users)}")
    if unknown_products:
        issues.append(f"Unknown product IDs: {len(unknown_products)}")

    report = pd.DataFrame({
        "metric": [
            "users", "products", "interactions", "missing_values",
            "duplicate_user_product_pairs", "issue_count"
        ],
        "value": [
            len(users), len(products), len(interactions),
            int(users.isna().sum().sum() + products.isna().sum().sum() + interactions.isna().sum().sum()),
            int(duplicate_pairs.sum()), len(issues),
        ],
    })
    return len(issues) == 0, issues, report
