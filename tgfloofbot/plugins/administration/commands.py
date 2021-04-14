from typing import List, Optional, Union

import pydantic
import telegram
import datetime
import typing
from datetime import timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ParseMode
from telegram.ext import CallbackContext, CallbackQueryHandler

from ... import loader

from ...client import TGFloofbotClient
from ...helpers import em
from ...logger import LOG

from . import models
from . import exceptions


class WarnCommandArgs(pydantic.BaseModel):
    bad_user: str = pydantic.Field(..., description="A raw user ID")
    warn_message: str = pydantic.Field(..., description="The warning reason")


class UsernoteCommandArgs(pydantic.BaseModel):
    bad_user: str = pydantic.Field(..., description="A raw user ID")
    warn_message: str = pydantic.Field(..., description="The note")


@loader.command(name="warn", help="warn a user", admin=True)
def warn_command(
    client: TGFloofbotClient,
    update: Update,
    context: CallbackContext,
    args: WarnCommandArgs,
) -> None:
    warn_helper(client, update, context, args, False)


@loader.command(name="note", help="adds a moderation note for a user", admin=True)
def usernote_command(
    client: TGFloofbotClient,
    update: Update,
    context: CallbackContext,
    args: UsernoteCommandArgs,
) -> None:
    warn_helper(client, update, context, args, True)


def warn_helper(
    client: TGFloofbotClient,
    update: Update,
    context: CallbackContext,
    args: Union[UsernoteCommandArgs, WarnCommandArgs],
    is_note: bool,
) -> None:
    user = update.effective_user
    chat = update.effective_chat
    try:
        main_group = client.updater.bot.get_chat(chat_id=client.config.main_group)
    except telegram.error.TelegramError:
        LOG.critical(
            "Unable to resolve the group ID set in the config! Warning commands not usable!"
        )
        return

    if main_group.type != "group":  # group only command
        context.bot.send_message(
            chat_id=chat, text="This command can only be used for groups."
        )
        return

    try:
        bad_user = client.updater.bot.get_chat_member(chat_id=main_group.id, user_id=args.bad_user).user  # type: ignore
        reason = args.warn_message
    except telegram.error.BadRequest:
        raise exceptions.UserNotFoundException(args.bad_user)
        return

    warning_entry = models.Warning(
        user_id=bad_user.id,
        date_added=datetime.datetime.now(timezone.utc),
        warned_by=user.username,
        warned_by_id=user.id,
        reason=reason,
    )

    if is_note:
        warning_entry.is_usernote = True

    client.db.add(warning_entry)
    client.db.commit()

    context.bot.send_message(
        chat_id=chat.id,
        text=f"*⚠️ User {em(bad_user.name)} {'noted' if is_note else 'warned'} by {em(user.username)} with reason {em(reason)}\.*",
        parse_mode="MarkdownV2",
    )

    if not is_note:
        try:
            context.bot.send_message(
                chat_id=bad_user.id,
                text=f"You have been warned in *{em(main_group.title)}*\. Reason: *{em(reason)}*",
                parse_mode="MarkdownV2",
            )
        except Exception as err:
            raise exceptions.WarningReasonDeliveryException(err)
