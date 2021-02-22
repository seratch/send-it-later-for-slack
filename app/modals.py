import datetime
import json
import os
from typing import Optional

from slack_bolt import BoltContext
from slack_sdk import WebClient

from .utils import date, time_minutes_later, tz_info


def show_installation_modal(client: WebClient, trigger_id: str):
    app_install_url = os.environ.get("APP_INSTALL_URL") or "https://j.mp/send-it-later"
    client.views_open(
        trigger_id=trigger_id,
        view={
            "type": "modal",
            "callback_id": "failure",
            "close": {"type": "plain_text", "text": "Cancel"},
            "title": {"type": "plain_text", "text": "Install This App!"},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Connect your Slack account with this app first!",
                    },
                    "accessory": {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Install This App"},
                        "value": "link-click",
                        "url": app_install_url,
                        "action_id": "link-button",
                    },
                }
            ],
        },
    )


def update_home_tab(client: WebClient, context: BoltContext, tz_offset: int):
    schedule_messages = (
        client.chat_scheduledMessages_list(token=context.user_token)
        if context.user_token
        else None
    )
    blocks = []
    blocks.append(
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Schedule a message :point_right:"},
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "New",
                },
                "value": "edit",
                "style": "primary",
                "action_id": "schedule-new-message-button",
            },
        }
    )
    if schedule_messages is not None:
        for msg in schedule_messages["scheduled_messages"]:
            time = datetime.datetime.fromtimestamp(
                msg["post_at"], tz=tz_info(tz_offset)
            )
            blocks.append({"type": "divider"})
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{msg['text']}\n\n_This message will be posted in <#{msg['channel_id']}> at {time}_",
                    },
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Delete",
                        },
                        "value": f"{msg['channel_id']}_{msg['id']}",
                        "style": "danger",
                        "action_id": "delete-scheduled-message-button",
                    },
                }
            )
    client.views_publish(
        user_id=context.user_id, view={"type": "home", "blocks": blocks}
    )


def build_modal_view(message: Optional[dict], tz_offset: int):
    modal = {
        "type": "modal",
        "callback_id": "schedule-new-message",
        "submit": {"type": "plain_text", "text": "Submit"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "title": {"type": "plain_text", "text": "Schedule a new message"},
        "private_metadata": json.dumps(message) if message is not None else "",
    }
    blocks = []
    if message is None:
        blocks.append(
            {
                "type": "input",
                "block_id": "message",
                "label": {"type": "plain_text", "text": "Message"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "input",
                    "multiline": True,
                },
            }
        )
    else:
        if "blocks" in message:
            blocks.extend(message["blocks"])
        else:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": message.get("text")},
                }
            )

    blocks.extend(
        [
            {
                "type": "input",
                "block_id": "date",
                "label": {"type": "plain_text", "text": "Date"},
                "element": {
                    "type": "datepicker",
                    "action_id": "input",
                    "initial_date": date(tz_offset, 10),
                    "placeholder": {"type": "plain_text", "text": "Select a date"},
                },
            },
            {
                "type": "input",
                "block_id": "time",
                "label": {"type": "plain_text", "text": "Time"},
                "element": {
                    "type": "timepicker",
                    "action_id": "input",
                    "initial_time": time_minutes_later(tz_offset, 10),
                    "placeholder": {"type": "plain_text", "text": "Select time"},
                },
            },
            {
                "type": "input",
                "block_id": "channel",
                "element": {
                    "type": "channels_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select the channel to post this message",
                    },
                    "action_id": "input",
                },
                "label": {"type": "plain_text", "text": "Channel"},
            },
        ]
    )
    modal["blocks"] = blocks
    return modal
