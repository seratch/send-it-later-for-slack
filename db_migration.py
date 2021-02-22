import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.debug("Database migration started ...")

from app.database import run_db_migration

run_db_migration()

logger.debug("... Completed.")
