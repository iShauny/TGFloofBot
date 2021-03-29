import argparse
import functools
import shlex
import typing

from typing import Any, Callable, Dict, List, Optional, Union

import pydantic
import telegram.ext
import yaml

from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler

from . import client
from . import exceptions
from . import helpers
from . import models

from .helpers import em

from .logger import LOG


commands: Dict[str, models.CommandData] = dict()
query_handlers: List[Callable] = list()
custom_loaders: List[Callable] = list()


ARGUMENT_TYPES = {
    "integer": int,
    "number": float,
    "string": str,
}


ARGUMENT_TYPE_NAMES = {
    int: "integer",
    float: "number",
    str: "text",
}


def get_command_help_text(command_data: models.CommandData) -> str:
    help_data = command_data.help_data
    arguments_text_name: List[str] = list()
    arguments_text_help: List[str] = list()

    for argument_help in help_data.arguments.values():
        arguments_text_name.append(em(argument_help.name))
        optional_text = f"optional " if argument_help.optional else ""
        default_text = (
            em(f" [default: {argument_help.default}]") if argument_help.default else ""
        )
        description_text = (
            f": {argument_help.description}" if argument_help.description else ""
        )
        arguments_text_help.append(
            em(f"({optional_text}{em(argument_help.data_type)})")
            + f"{default_text}{description_text}"
        )

    help_text_lines: List[str] = list()
    if help_data.description:
        help_text_lines.append(f"{help_data.description}\n")
    syntax_arguments = (
        f" {em(' '.join(arguments_text_name))}" if arguments_text_name else ""
    )
    help_text_lines.append(f"Syntax: `/{command_data.name}{syntax_arguments}`")
    if arguments_text_name:
        help_text_lines.append(f"\nArguments:")
        for arg_name, arg_help in zip(arguments_text_name, arguments_text_help):
            help_text_lines.append(f" \u2022 `{arg_name}` {arg_help}")

    return "\n".join(help_text_lines)


class CommandArgParser(argparse.ArgumentParser):
    def error(self, message):
        raise SyntaxError(message)


def command(
    function: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    help: Optional[str] = None,
) -> Callable:
    """Decorator for tagging functions as commands"""
    if not function:
        return functools.partial(command, name=name, help=help)

    name = name or function.__name__
    if name in commands:
        raise exceptions.FloofbotLoaderException(
            "Duplicate command found: {name} ({function})"
        )
    LOG.debug(f"Registering command handler: {name}")

    ## Set up argument parsing
    parser = None
    parse = typing.get_type_hints(function).get("args")
    command_help_data = models.CommandHelpData(
        name=name, description=help, arguments=dict()
    )

    if parse:
        model_schema = parse.schema()
        parser = CommandArgParser()
        for argument_name, argument_data in model_schema["properties"].items():
            argument_type = ARGUMENT_TYPES.get(argument_data.get("type"))
            if argument_type is None:
                raise exceptions.FloofbotLoaderException(
                    f"Argument '{argument_name}' has unsupported data type: {argument_data.get('type')}"
                )

            argument_hint = typing.get_type_hints(parse)[argument_name]
            is_optional = "default" in argument_data or (
                typing.get_origin(argument_hint) is Union
                and type(None) in typing.get_args(argument_hint)
            )

            command_help_data.arguments[argument_name] = models.CommandArgumentHelpData(
                name=argument_name,
                description=argument_data.get("description"),
                optional=is_optional,
                default=argument_data.get("default"),
                data_type=ARGUMENT_TYPE_NAMES[argument_type],
            )
            parser.add_argument(
                argument_name,
                type=argument_type,
                default=argument_data.get("default"),
                nargs="?" if is_optional else None,
            )

    commands[name] = command_data = models.CommandData(
        function=function,
        name=name,
        parse=parse,
        help_data=command_help_data,
    )

    def wrapped_callback(update: Update, context: CallbackContext) -> Callable:
        LOG.debug(f"Command invoked: {name}")
        kwargs = dict()
        if parser:
            message_entities = update.effective_message.entities
            shlex_split = shlex.split(
                update.effective_message.text[message_entities[0].length :]
            )
            try:
                parsed_args = parser.parse_args(shlex_split)
                kwargs["args"] = parse(**vars(parsed_args))
            except Exception as err:
                LOG.exception(f"Parsing exception: {err}")
                parsing_error_text = em(f"Invalid command syntax: {err}")
                usage_text = get_command_help_text(command_data)
                raise exceptions.FloofbotSyntaxError(
                    f"{parsing_error_text}\n\n{usage_text}"
                )
        return function(client.global_client, update, context, **kwargs)

    if client.global_client:
        handler = telegram.ext.CommandHandler(name, wrapped_callback)
        client.global_client.dispatcher.add_handler(handler)

    return function


def callback_query_handler(
    function: Optional[Callable] = None,
    *,
    key: str,
) -> Callable:
    """Decorator for registering custom callback query handlers"""
    if not function:
        return functools.partial(callback_query_handler, key=key)
    query_handlers.append(function)

    helpers.check_valid_client()
    parse = typing.get_type_hints(function).get("args")

    def wrapped_callback(update: Update, context: CallbackContext) -> Callable:
        LOG.debug(f"Wrapped callback called: {function.__name__}")
        query = update.callback_query
        query.answer()
        cleaned_data = context.matches[0].groups()[0]
        function_kwargs: Dict[str, Union[str, pydantic.BaseModel]] = dict()
        if parse is str:
            function_kwargs["args"] = cleaned_data
        elif issubclass(parse, pydantic.BaseModel):
            LOG.debug(yaml.safe_load(cleaned_data))
            function_kwargs["args"] = parse(**yaml.safe_load(cleaned_data))
        return function(client.global_client, update, context, **function_kwargs)

    query_handler = CallbackQueryHandler(
        wrapped_callback, pattern=f"^{key};([\\s\\S]+)$"
    )
    client.global_client.dispatcher.add_handler(query_handler)

    return function


def custom(function: Optional[Callable] = None) -> Callable:
    """Decorator for collecting custom loaders"""
    if not function:
        return functools.partial(custom)
    custom_loaders.append(function)
    return function
