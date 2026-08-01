from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class SnowflakeSettings:
    account: str
    user: str
    password: str
    role: str
    warehouse: str
    database: str
    schema: str


def get_snowflake_settings() -> SnowflakeSettings:
    required = {
        "SNOWFLAKE_ACCOUNT": os.getenv("SNOWFLAKE_ACCOUNT", ""),
        "SNOWFLAKE_USER": os.getenv("SNOWFLAKE_USER", ""),
        "SNOWFLAKE_PASSWORD": os.getenv("SNOWFLAKE_PASSWORD", ""),
        "SNOWFLAKE_WAREHOUSE": os.getenv("SNOWFLAKE_WAREHOUSE", ""),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            "다음 환경변수를 .env에 입력하십시오: " + ", ".join(missing)
        )

    return SnowflakeSettings(
        account=required["SNOWFLAKE_ACCOUNT"],
        user=required["SNOWFLAKE_USER"],
        password=required["SNOWFLAKE_PASSWORD"],
        role=os.getenv("SNOWFLAKE_ROLE", "SYSADMIN"),
        warehouse=required["SNOWFLAKE_WAREHOUSE"],
        database=os.getenv("SNOWFLAKE_DATABASE", "KIRI_AI_DEMO"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "MART"),
    )
