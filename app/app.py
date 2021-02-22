import logging
import os

from .listeners import register_listeners

logging.basicConfig(level=logging.DEBUG)

user_token = os.environ.get("SLACK_USER_TOKEN")
logger = logging.getLogger(__name__)

if user_token is None or len(user_token) == 0:
    from .app_oauth import app, installation_store
    from .database import engine

    register_listeners(
        app=app,
        installation_store=installation_store,
        engine=engine,
    )
else:
    from .app_single_workspace import app

    register_listeners(
        app=app,
        single_user_token=user_token,
    )
