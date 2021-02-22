import logging
import os
from typing import Optional

import sqlalchemy
from slack_sdk.oauth.installation_store import InstallationStore
from slack_sdk.oauth.installation_store.sqlalchemy import SQLAlchemyInstallationStore
from slack_sdk.oauth.state_store.sqlalchemy import SQLAlchemyOAuthStateStore
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

user_token = os.environ.get("SLACK_USER_TOKEN")
engine: Optional[Engine] = None
installation_store: Optional[InstallationStore] = None

client_id = os.environ["SLACK_CLIENT_ID"]

local_database_url = "sqlite:///local_dev.db"
database_url = os.environ.get("DATABASE_URL") or local_database_url
logger.info(f"database: {database_url}")

logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
engine = sqlalchemy.create_engine(database_url)
installation_store = SQLAlchemyInstallationStore(
    client_id=client_id,
    engine=engine,
    logger=logger,
)
oauth_state_store = SQLAlchemyOAuthStateStore(
    expiration_seconds=120,
    engine=engine,
    logger=logger,
)


def run_db_migration():
    try:
        engine.execute("select count(*) from slack_bots")
    except Exception as _:
        installation_store.metadata.create_all(engine)
        oauth_state_store.metadata.create_all(engine)


if database_url == local_database_url:
    run_db_migration()
