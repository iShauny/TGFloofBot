from typing import List, Optional

import pydantic
import telegram

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ParseMode
from telegram.ext import CallbackContext, CallbackQueryHandler

from ... import loader

from ...client import TGFloofbotClient
from ...helpers import em
from ...logger import LOG

from . import models
from . import exceptions


@loader.command(help="Checks if the bot is alive")
def ping(client: TGFloofbotClient, update: Update, context: CallbackContext) -> None:
    ## TODO: Measure approximate latency by sending a message, receiving it, then editing it
    context.bot.send_message(chat_id=update.effective_chat.id, text="Pong!")


class IDCommandArgs(pydantic.BaseModel):
    identifier: Optional[str] = pydantic.Field(
        None, description="Either a raw user ID or mention"
    )


@loader.command(name="id", help="Shows the user's ID number")
def id_command(
    client: TGFloofbotClient,
    update: Update,
    context: CallbackContext,
    args: IDCommandArgs,
) -> None:
    entities = update.effective_message.entities
    user = update.effective_user

    if len(entities) > 1 and entities[1].type in ("text_mention", "mention"):
        user = entities[1].user
    elif args.identifier:
        try:
            user = context.bot.get_chat(args.identifier)  # type: ignore
        except telegram.error.BadRequest:
            raise exceptions.UserNotFoundException(args.identifier)

    user_id = user.id
    full_name = user.full_name
    text = f"User ID for [@{full_name}](tg://user?id={user_id}): `{user_id}`"
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=text, parse_mode=ParseMode.MARKDOWN_V2
    )


@loader.custom
def help_custom(client: TGFloofbotClient):

    MAX_COMMANDS_PER_PAGE = 5

    class HelpCommandArgs(pydantic.BaseModel):
        command: Optional[str] = pydantic.Field(
            None, description=em("Name of the command")
        )

    class HelpMenuButtonArgs(pydantic.BaseModel):
        a: str = pydantic.Field(
            ...,
            description="Button action. Must be 'p' (previous) or 'n' (next)",
        )

    buttons = [
        [
            InlineKeyboardButton("Previous", callback_data="help_menu_page;a: p"),
            InlineKeyboardButton("Next", callback_data="help_menu_page;a: n"),
        ],
    ]
    button_reply_markup = InlineKeyboardMarkup(buttons)

    def generate_commands_help_page(page_index: int) -> str:
        """Helper function for generating a page displaying the list of commands"""
        all_commands: List[str] = list()
        for command_data in loader.commands.values():
            if command_data.help_data.description:
                description = f": {command_data.help_data.description}"
            else:
                description = ""
            all_commands.append(f"/{command_data.name}{description}")
        all_commands.sort()
        segments = list(
            all_commands[it : it + MAX_COMMANDS_PER_PAGE]
            for it in range(0, len(all_commands), MAX_COMMANDS_PER_PAGE)
        )
        page_text = f"Commands list: page {page_index + 1}/{len(segments)}\n"
        page_text += "\n".join(segments[page_index])
        return page_text

    @loader.command(
        help="Shows the help text of a command or lists all commands", name="help"
    )
    def help_command(
        client: TGFloofbotClient,
        update: Update,
        context: CallbackContext,
        args: HelpCommandArgs,
    ) -> None:
        if args.command is None:
            text = generate_commands_help_page(0)
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=button_reply_markup,
            )
        else:
            command_name = args.command.casefold()
            command_data = loader.commands.get(command_name)
            if command_data:
                text = loader.get_command_help_text(command_data)
            else:
                text = f"Command `{em(command_name)}` not found"
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                parse_mode=ParseMode.MARKDOWN_V2,
            )

    @loader.callback_query_handler(key="help_menu_page")
    def help_command_query_handler(
        client: TGFloofbotClient,
        update: Update,
        context: CallbackContext,
        args: HelpMenuButtonArgs,
    ) -> None:
        message = update.callback_query.message
        header_text = message.text.splitlines()[0]
        current_page_number = int(header_text.rsplit(" ", 1)[-1].split("/")[0])
        delta = 1 if args.a == "n" else -1
        page_index = current_page_number + delta - 1
        max_index = int((len(loader.commands) - 1) / MAX_COMMANDS_PER_PAGE)
        if page_index > max_index:
            page_index = 0
        elif page_index < 0:
            page_index = max_index
        update.callback_query.edit_message_text(
            text=generate_commands_help_page(page_index),
            reply_markup=button_reply_markup,
        )
