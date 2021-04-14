from typing import List, Optional

import pydantic
import telegram
import datetime
from datetime import timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ParseMode
from telegram.ext import CallbackContext, CallbackQueryHandler

from ... import loader

from ...client import TGFloofbotClient
from ...helpers import em
from ...logger import LOG

from . import models
from . import exceptions

@loader.custom
def administration_custom(client: TGFloofbotClient):

    admin_group_id = client.config.main_group

    def _resolve_admin_group_id(update):
        try:
            admin_group = client.updater.bot.get_chat(chat_id=admin_group_id)
        except telegram.error.TelegramError:
            LOG.critical("Unable to resolve the group ID set in the config! Defaulting to context group ID.")
            admin_group = update.effective_chat

        return admin_group

    class WarnCommandArgs(pydantic.BaseModel):
        bad_user: str = pydantic.Field(
            None, description="A raw user ID")
        warn_message: str = pydantic.Field(
            None, description="The warning reason")

    class UsernoteCommandArgs(pydantic.BaseModel):
        bad_user: Optional[str] = pydantic.Field(
            None, description="A raw user ID")
        warn_message: Optional[str] = pydantic.Field(
            None, description="The note")

    @loader.command(name="warn", help="warn a user", admin=True)
    def warn_command(
        client: TGFloofbotClient,
        update: Update,
        context: CallbackContext,
        args: WarnCommandArgs
    ) -> None:
        warn_helper(client, update, context, args, False)
        return

    @loader.command(name="note", help="adds a moderation note for a user", admin=True)
    def usernote_command(
        client: TGFloofbotClient,
        update: Update,
        context: CallbackContext,
        args: UsernoteCommandArgs
    ) -> None:
        warn_helper(client, update, context, args, True)
        return

    def warn_helper(client, update, context, args, is_note):
        user = update.effective_user
        chat = update.effective_chat
        admin_chat = _resolve_admin_group_id(Update)

        if admin_chat.type != "group":  # group only command
            context.bot.send_message(chat_id=chat, text="This command can only be used for groups.")
            return
        
        try:
            bad_user = client.updater.bot.get_chat_member(chat_id=admin_chat.id, user_id=args.bad_user).user  # type: ignore
            reason = args.warn_message
        except telegram.error.BadRequest:
            raise exceptions.UserNotFoundException(args.bad_user)
            return

        try:
            warning_entry = models.Warning(
                user_id=bad_user.id,
                date_added=datetime.datetime.now(timezone.utc),
                warned_by=user.username,
                warned_by_id=user.id,
                reason=reason
            )

            if is_note:
                warning_entry.is_usernote = True

            client.db.add(warning_entry)
            client.db.commit()

        except Exception as e:
            LOG.error(f"Error occurred when attempting to insert a {'warning' if is_note is False else 'usernote'} into the database: " + str(e))
            context.bot.send_message(chat_id=chat.id, text=f"A fatal error occurred trying to insert the {'warning' if is_note is False else 'usernote'} into the database.")
            return
        if not is_note:
            try: 
                context.bot.send_message(chat_id=bad_user.id, text=f"You have been warned in *{admin_chat.title}*\. Reason: *{reason}*", parse_mode="MarkdownV2")
            except Exception:
                context.bot.send_message(chat_id=chat.id, text="Unable to DM the user to notify them of their warning.")

        context.bot.send_message(chat_id=chat.id, text=f"*⚠️ User {bad_user.name} {'warned' if is_note is False else 'noted'} by {user.username} with reason {reason}\.*", parse_mode="MarkdownV2")



