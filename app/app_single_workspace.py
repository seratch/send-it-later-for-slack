import os

from slack_bolt import App

user_token = os.environ.get("SLACK_USER_TOKEN")

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)
