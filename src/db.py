from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import pandas as pd
import snowflake.connector

from src.config import get_snowflake_settings


@contextmanager
def snowflake_connection() -> Iterator[snowflake.connector.SnowflakeConnection]:
    settings = get_snowflake_settings()
    connection = snowflake.connector.connect(
        account=settings.account,
        user=settings.user,
        password=settings.password,
        role=settings.role,
        warehouse=settings.warehouse,
        # 최초 실행 시 KIRI_AI_DEMO 데이터베이스가 아직 없으므로
        # 접속 단계에서는 database/schema를 지정하지 않습니다.
        # 모든 SQL은 완전한 객체명(DB.SCHEMA.TABLE)을 사용합니다.
        session_parameters={"QUERY_TAG": "KIRI_AI_DEMO"},
    )
    try:
        yield connection
    finally:
        connection.close()


def query_dataframe(sql: str, params: tuple | None = None) -> pd.DataFrame:
    with snowflake_connection() as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(sql, params or ())
            return cursor.fetch_pandas_all()
        finally:
            cursor.close()
