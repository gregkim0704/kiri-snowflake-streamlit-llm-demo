from __future__ import annotations

from pathlib import Path

import pandas as pd
from snowflake.connector.pandas_tools import write_pandas

from src.db import snowflake_connection


DATA_PATH = Path("data/daily_nav.csv")
SETUP_SQL_PATH = Path("sql/01_setup_objects.sql")
TRANSFORM_SQL_PATH = Path("sql/02_transform.sql")


def execute_sql_file(connection, path: Path) -> None:
    sql_text = path.read_text(encoding="utf-8")
    connection.execute_string(sql_text)
    print(f"[정상] SQL 실행: {path}")


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "data/daily_nav.csv가 없습니다. "
            "먼저 python 01_generate_sample_data.py를 실행하십시오."
        )

    dataframe = pd.read_csv(DATA_PATH)
    dataframe["TRADE_DATE"] = pd.to_datetime(
        dataframe["TRADE_DATE"]
    ).dt.date

    expected_columns = {
        "TRADE_DATE",
        "FUND_ID",
        "NAV",
        "BENCHMARK_NAV",
    }
    if set(dataframe.columns) != expected_columns:
        raise ValueError(
            f"CSV 컬럼이 예상과 다릅니다: {list(dataframe.columns)}"
        )

    if dataframe.duplicated(
        subset=["TRADE_DATE", "FUND_ID"]
    ).any():
        raise ValueError("TRADE_DATE와 FUND_ID 기준 중복이 있습니다.")

    if dataframe.isna().any().any():
        raise ValueError("CSV에 결측값이 있습니다.")

    with snowflake_connection() as connection:
        execute_sql_file(connection, SETUP_SQL_PATH)

        cursor = connection.cursor()
        try:
            cursor.execute(
                "TRUNCATE TABLE KIRI_AI_DEMO.RAW.DAILY_NAV"
            )
        finally:
            cursor.close()

        success, chunks, rows, _ = write_pandas(
            connection,
            dataframe,
            table_name="DAILY_NAV",
            database="KIRI_AI_DEMO",
            schema="RAW",
            auto_create_table=False,
            overwrite=False,
            quote_identifiers=False,
        )

        if not success:
            raise RuntimeError("Snowflake 적재에 실패했습니다.")

        print(
            f"[정상] Snowflake 적재: {rows:,}행, {chunks}개 청크"
        )

        execute_sql_file(connection, TRANSFORM_SQL_PATH)

        cursor = connection.cursor()
        try:
            cursor.execute(
                """
                SELECT *
                FROM KIRI_AI_DEMO.MART.V_FUND_SUMMARY
                ORDER BY FUND_ID
                """
            )
            summary = cursor.fetch_pandas_all()
        finally:
            cursor.close()

    print("[정상] 성과·위험지표 계산 완료")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
