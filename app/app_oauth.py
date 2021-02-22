import logging
import os

from slack_bolt import App
from slack_bolt.oauth.oauth_settings import OAuthSettings

from app.database import (
    oauth_state_store,
    installation_store,
)

logger = logging.getLogger(__name__)
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

user_token = os.environ.get("SLACK_USER_TOKEN")

client_id, client_secret, signing_secret = (
    os.environ["SLACK_CLIENT_ID"],
    os.environ.get("SLACK_CLIENT_SECRET"),
    os.environ.get("SLACK_SIGNING_SECRET"),
)

app = App(
    logger=logger,
    signing_secret=signing_secret,
    oauth_settings=OAuthSettings(
        install_page_rendering_enabled=False,
        client_id=client_id,
        client_secret=client_secret,
        installation_store=installation_store,
        state_store=oauth_state_store,
    ),
)
