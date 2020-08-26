import asyncpg

from common import config
from common.tlog import tlog


async def create_db_connection(dsn: str = None) -> None:
    config.db_conn_pool = await asyncpg.create_pool(
        dsn=dsn if dsn else config.dsn, min_size=2, max_size=10
    )
    tlog("db connection pool initialized")