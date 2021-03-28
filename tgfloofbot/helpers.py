from typing import Any

import telegram

from . import client
from . import exceptions


def em(text: Any, version: int = 2, entity_type: str = None) -> str:
    """Helper wrapper for escaping markdown text."""
    return telegram.utils.helpers.escape_markdown(
        str(text), version=version, entity_type=entity_type
    )


def check_valid_client() -> None:
    """Helper to check if the client is available"""
    if client.global_client is None:
        raise exceptions.FloofbotLoaderException("No bot client has been created yet")
