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
        bad_user: Optional[str] = pydantic.Field(
            None, description="Either a raw user ID or mention")
        warn_message: Optional[str] = pydantic.Field(
            None, description="The warning reason")

    @loader.command(name="warn", help="warn a user", admin=True)
    def warn_command(
        client: TGFloofbotClient,
        update: Update,
        context: CallbackContext,
        args: WarnCommandArgs
    ) -> None:
        entities = update.effective_message.entities
        user = update.effective_user
        chat = update.effective_chat
        admin_chat = _resolve_admin_group_id(Update)

        if admin_chat.type != "group":  # group only command
            context.bot.send_message(chat_id=chat, text="This command can only be used for groups.")
            return
        
        if len(entities) > 1 and entities[1].type in ("text_mention", "mention"):
            bad_user = client.updater.bot.get_chat_member(chat_id=admin_chat.id, user_id=entities[1].user.id)
            if args.warn_message:
                reason = args.warn_message
            else:
                reason = "No reason provided."
        elif args.bad_user:
            try:
                bad_user = client.updater.bot.get_chat_member(chat_id=admin_chat.id, user_id=args.bad_user).user  # type: ignore
                if args.warn_message:
                    reason = args.warn_message
                else:
                    reason = "No reason provided."
            except telegram.error.BadRequest:
                raise exceptions.UserNotFoundException(args.bad_user)
                return
        else: 
            context.bot.send_message(chat_id=chat.id, text="Invalid arguments. Please provide a user ID/mention and a reason.")
            return

        context.bot.send_message(chat_id=chat.id, text=f"{bad_user.id}")
        try:
            warning_entry = models.Warning(
                user_id=bad_user.id,
                date_added=datetime.datetime.now(timezone.utc),
                warned_by=user.username,
                warned_by_id=user.id,
                reason=reason
            )

            client.db.add(warning_entry)
            client.db.commit()

        except Exception as e:
            LOG.error("Error occurred when attempting to insert a warning into the database: " + str(e))
            context.bot.send_message(chat_id=chat.id, text="A fatal error occurred trying to insert the warning into the database.")
            return

        try: 
            context.bot.send_message(chat_id=bad_user.id, text=f"You have been warned in {admin_chat.title} by {user.username}. Reason: {reason}")
        except Exception:
            context.bot.send_message(chat_id=chat.id, text="Unable to DM the user to notify them of their warning.")

        context.bot.send_message(chat_id=chat.id, text=f"⚠️ | User {bad_user.name} warned by {user.username} with reason {reason}.")

