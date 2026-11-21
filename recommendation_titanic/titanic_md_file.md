# Mapping Manifesto

## Source tables: `schema_1`

- `users`: user_id, age_group, region, ingested_at
- `products`: product_id, category, price, popularity_score, ingested_at
- `interactions`: user_id, product_id, rating, event_type, event_timestamp

## Target tables: `schema_2`

### `recommendation_features`

Anchor: `schema_1.interactions`

| Target field | Source/logic | Type |
|---|---|---|
| user_id | interactions.user_id | Direct |
| product_id | interactions.product_id | Direct |
| rating | interactions.rating | Direct |
| category | products.category via product_id | Joined |
| price | products.price via product_id | Joined |
| popularity_score | products.popularity_score via product_id | Joined |
| user_activity_count | COUNT(product_id) by user_id | Aggregated |
| average_rating_per_user | AVG(rating) by user_id | Aggregated |
| item_rating_count | COUNT(rating) by product_id | Aggregated |
| average_rating_per_item | AVG(rating) by product_id | Aggregated |
| rating_normalized | (rating - 1) / 4 | Derived |

### `user_features`

Anchor: `schema_1.interactions`

- `user_activity_count`: count of interactions per user
- `average_rating_per_user`: mean rating per user

### `item_features`

Anchor: `schema_1.interactions`

- `item_rating_count`: count of ratings per product
- `average_rating_per_item`: mean rating per product
