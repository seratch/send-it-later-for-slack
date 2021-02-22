import datetime
import json
from logging import Logger
from typing import Optional, Callable

from slack_bolt import App, Ack, BoltContext
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.oauth import InstallationStore
from sqlalchemy import and_
from sqlalchemy.engine import Engine

from .modals import (
    update_home_tab,
    show_installation_modal,
    build_modal_view,
)
from .utils import built_post_at, tz_info


def register_listeners(
    app: App,
    single_user_token: Optional[str] = None,
    installation_store: Optional[InstallationStore] = None,
    engine: Optional[Engine] = None,
):
    @app.middleware
    def print_request(body, logger, next):
        logger.info(body)
        next()

    if single_user_token is not None:

        @app.middleware
        def set_user_token_to_context(context: BoltContext, next: Callable):
            context["user_token"] = single_user_token
            next()

    @app.event("app_home_opened")
    def handle_app_home_opened(event: dict, context: BoltContext, client: WebClient):
        if event["tab"] == "home":
            if context.user_token is not None:
                user_info = client.users_info(
                    token=context.user_token, user=context.user_id
                )
                tz_offset = user_info["user"]["tz_offset"]
                update_home_tab(client, context, tz_offset)
            else:
                update_home_tab(client, context, 0)

    @app.shortcut("send-this-message-later")
    def handle_message_shortcut(
        ack: Ack, body: dict, context: BoltContext, logger: Logger, client: WebClient
    ):
        ack()

        if context.user_token is None:
            show_installation_modal(client, body["trigger_id"])
            return

        message = body["message"]
        text, attachments, blocks = (
            message.get("text", ""),
            message.get("attachments"),
            message.get("blocks"),
        )
        message = {"text": text, "channel": context.channel_id}
        if attachments is not None:
            message["attachments"] = attachments
        if blocks is not None:
            blocks = [b for b in blocks if b["type"] != "rich_text"]
            if len(blocks) > 0:
                message["blocks"] = blocks

        user_info = client.users_info(token=context.user_token, user=context.user_id)
        tz_offset = user_info["user"]["tz_offset"]
        try:
            client.views_open(
                trigger_id=body["trigger_id"],
                view=build_modal_view(message, tz_offset),
            )
        except Exception as _:
            logger.exception("Failed to open a modal")
            client.views_open(
                trigger_id=body["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "failure",
                    "close": {"type": "plain_text", "text": "Cancel"},
                    "title": {"type": "plain_text", "text": "Unsupported Message Type"},
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "Sorry, I cannot schedule this message! :bow:",
                            },
                        }
                    ],
                },
            )

    @app.action("schedule-new-message-button")
    def open_new_message_modal(
        ack: Ack, body: dict, context: BoltContext, client: WebClient
    ):
        ack()
        if context.user_token is None:
            show_installation_modal(client, body["trigger_id"])
            return

        user_info = client.users_info(token=context.user_token, user=context.user_id)
        tz_offset = user_info["user"]["tz_offset"]

        client.views_open(
            trigger_id=body["trigger_id"],
            view=build_modal_view(None, tz_offset),
        )

    @app.view("schedule-new-message")
    def save_scheduled_message(
        body: dict,
        ack: Ack,
        context: BoltContext,
        client: WebClient,
    ):
        user_info = client.users_info(token=context.user_token, user=context.user_id)
        tz_offset = user_info["user"]["tz_offset"]

        submitted_data = body["view"]["state"]["values"]
        channel, message_text, date, time = (
            submitted_data["channel"]["input"]["selected_channel"],
            submitted_data.get("message", {}).get("input", {}).get("value"),
            submitted_data["date"]["input"]["selected_date"],
            submitted_data["time"]["input"]["selected_time"],
        )
        message = {"text": message_text}
        message_str = body["view"]["private_metadata"]
        if len(message_str) > 0:
            message = json.loads(message_str)

        post_at = built_post_at(tz_offset, date, time)

        errors = {}
        if post_at <= datetime.datetime.now(tz=tz_info(tz_offset)):
            errors["date"] = "Set a future date"
            errors["time"] = "Set a future time"

        if len(errors):
            return ack(
                response_action="errors",
                errors=errors,
            )

        try:
            result = client.chat_scheduleMessage(
                token=context.user_token,
                channel=channel,
                text=message.get("text", ""),
                attachments=message.get("attachments"),
                blocks=message.get("blocks"),
                post_at=post_at.timestamp(),
            )
            ack()

            update_home_tab(client, context, tz_offset)

            if message.get("channel"):
                time = datetime.datetime.fromtimestamp(
                    result["post_at"], tz=tz_info(tz_offset)
                )
                client.chat_postEphemeral(
                    channel=message.get("channel"),
                    user=context.user_id,
                    text=f"_The message is scheduled to post in <#{result['channel']}> at {time}_",
                )

        except SlackApiError as e:
            if e.response["error"] == "not_in_channel":
                errors["channel"] = "You are not in the channel!"
            else:
                raise e

        if len(errors):
            return ack(
                response_action="errors",
                errors=errors,
            )

    @app.action("delete-scheduled-message-button")
    def delete_scheduled_message(
        ack: Ack, action: dict, context: BoltContext, client: WebClient
    ):
        channel, message_id = action["value"].split("_")
        client.chat_deleteScheduledMessage(
            token=context.user_token,
            channel=channel,
            scheduled_message_id=message_id,
        )
        ack()
        user_info = client.users_info(token=context.user_token, user=context.user_id)
        tz_offset = user_info["user"]["tz_offset"]
        update_home_tab(client, context, tz_offset)

    @app.event("tokens_revoked")
    def handle_revoked_tokens(event: dict, context: BoltContext):
        i = installation_store.installations
        with engine.begin() as conn:
            for user_id in event["tokens"]["oauth"]:
                conn.execute(
                    i.delete(
                        and_(i.c.user_id == user_id, i.c.team_id == context.team_id)
                    )
                )

    @app.event("app_uninstalled")
    def handle_revoked_tokens(context: BoltContext):
        with engine.begin() as conn:
            i = installation_store.installations
            conn.execute(i.delete(i.c.team_id == context.team_id))
            b = installation_store.bots
            conn.execute(b.delete(b.c.team_id == context.team_id))

    @app.action("link-button")
    def handle_link_button(ack: Ack):
        ack()
