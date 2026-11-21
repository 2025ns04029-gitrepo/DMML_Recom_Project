from sqlalchemy import inspect, text


def create_primary_key(engine, schema, table, columns):
    constraint = f"pk_{table}"
    joined = ", ".join(f'"{column}"' for column in columns)
    columns_sql = " ".join(f'"{column}"' for column in columns)
    with engine.begin() as conn:
        conn.execute(text(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = '{constraint}'
                      AND conrelid = '"{schema}"."{table}"'::regclass
                ) THEN
                    ALTER TABLE "{schema}"."{table}"
                    ADD CONSTRAINT "{constraint}" PRIMARY KEY ({joined});
                END IF;
            EXCEPTION WHEN duplicate_table THEN NULL;
            END $$;
        """))


def upsert_dataframe(engine, frame, schema, table, primary_keys):
    frame = frame.drop_duplicates(subset=primary_keys, keep="last")
    inspector = inspect(engine)
    exists = inspector.has_table(table, schema=schema)

    if not exists:
        frame.to_sql(table, engine, schema=schema, if_exists="replace", index=False)
        create_primary_key(engine, schema, table, primary_keys)
    else:
        staging = f"_staging_{table}"
        frame.to_sql(staging, engine, schema=schema, if_exists="replace", index=False)

        key_list = ", ".join(f'"{key}"' for key in primary_keys)
        columns = ", ".join(f'"{column}"' for column in frame.columns)
        staging_columns = ", ".join(f'"{column}"' for column in frame.columns)
        duplicate_condition = " AND ".join(
            f'a."{key}" = b."{key}"' for key in primary_keys
        )
        update_columns = [column for column in frame.columns if column not in primary_keys]
        conflict_update = ", ".join(
            f'"{column}" = EXCLUDED."{column}"' for column in update_columns
        )

        with engine.begin() as conn:
            if "uuid" in frame.columns:
                conn.execute(text(
                    f'ALTER TABLE "{schema}"."{table}" '
                    'ADD COLUMN IF NOT EXISTS "uuid" TEXT'
                ))
            conn.execute(text(f"""
                DELETE FROM "{schema}"."{table}" a
                USING "{schema}"."{table}" b
                WHERE {duplicate_condition}
                  AND a.ctid < b.ctid
            """))

        create_primary_key(engine, schema, table, primary_keys)

        with engine.begin() as conn:
            if conflict_update:
                conn.execute(text(f"""
                    INSERT INTO "{schema}"."{table}"
                    ({columns})
                    SELECT {staging_columns} FROM "{schema}"."{staging}"
                    ON CONFLICT ({key_list}) DO UPDATE SET {conflict_update}
                """))
            else:
                conn.execute(text(f"""
                    INSERT INTO "{schema}"."{table}"
                    SELECT * FROM "{schema}"."{staging}"
                    ON CONFLICT ({key_list}) DO NOTHING
                """))
            conn.execute(text(f'DROP TABLE IF EXISTS "{schema}"."{staging}"'))


def append_dataframe(engine, frame, schema, table, primary_keys=None):
    if primary_keys:
        upsert_dataframe(engine, frame, schema, table, primary_keys)
        return

    inspector = inspect(engine)
    if not inspector.has_table(table, schema=schema):
        frame.to_sql(table, engine, schema=schema, if_exists="replace", index=False)
    else:
        frame.to_sql(table, engine, schema=schema, if_exists="append", index=False)
