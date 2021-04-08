from typing import Any

import telegram

from . import client
from . import exceptions

from .logger import LOG


def em(text: Any, version: int = 2, entity_type: str = None) -> str:
    """Helper wrapper for escaping markdown text."""
    return telegram.utils.helpers.escape_markdown(
        str(text), version=version, entity_type=entity_type
    )


def check_valid_client() -> None:
    """Helper to check if the client is available"""
    if client.global_client is None:
        raise exceptions.FloofbotLoaderException("No bot client has been created yet")


def is_admin(client: "client.TGFloofbotClient", user_id: int) -> bool:
    """Helper to check if the given user is an admin"""
    bot = client.updater.bot
    for group_id in [client.config.main_group] + client.config.admin_groups:
        try:
            member = bot.get_chat_member(group_id, user_id)
            if member.status in (
                telegram.constants.CHATMEMBER_ADMINISTRATOR,
                telegram.constants.CHATMEMBER_CREATOR,
            ):
                return True
        except telegram.error.TelegramError as err:
            LOG.exception(f"Failed to get chat member: {err}")
    return False
