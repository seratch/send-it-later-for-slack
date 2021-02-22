import os

from app.app import app
from flask import Flask, request
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.adapter.socket_mode import SocketModeHandler

flask_app = Flask(__name__)
flask_handler = SlackRequestHandler(app)


@flask_app.route("/slack/install", methods=["GET"])
def install():
    return flask_handler.handle(request)


@flask_app.route("/slack/oauth_redirect", methods=["GET"])
def oauth_redirect():
    return flask_handler.handle(request)


app_token = os.environ.get("SLACK_APP_TOKEN")

if app_token is None:

    @flask_app.route("/slack/events", methods=["POST"])
    def slack_events():
        return flask_handler.handle(request)


else:
    socket_mode = SocketModeHandler(
        app=app,
        app_token=app_token,
        trace_enabled=True,
    )
    if app.oauth_flow is not None:
        socket_mode.connect()
    else:
        socket_mode.start()

if __name__ == "__main__":
    flask_app.run(port=3000, debug=True)
