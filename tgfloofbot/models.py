import dataclasses
import enum
import pathlib

from typing import Any, Callable, Dict, List, Optional

import pydantic

from sqlalchemy.ext.declarative import declarative_base


## Global base used for all ORM model definitions
ORMBase = declarative_base()


class LogFileConfig(pydantic.BaseModel):
    filename: pathlib.Path = pydantic.Field(
        pathlib.Path("bot.log"), description="Location of the log file"
    )
    maxBytes: int = pydantic.Field(500_000, description="Max size of one log file")
    backupCount: int = pydantic.Field(5, description="Number of log rotations")


class Config(pydantic.BaseSettings):
    token: str = pydantic.Field(..., description="Telegram bot API token")
    debug: bool = pydantic.Field(False, description="Show debug output")
    log: LogFileConfig = pydantic.Field(LogFileConfig(), description="Log config")
    database: pathlib.Path = pydantic.Field(..., description="Database file path")
    main_group: int = pydantic.Field(..., description="The main group ID")
    admin_groups: List[int] = pydantic.Field(
        list(), description="Admin group IDs for the main group"
    )


@dataclasses.dataclass
class CommandArgumentHelpData:
    name: str
    description: Optional[str]
    optional: bool
    default: Any
    data_type: str


@dataclasses.dataclass
class CommandHelpData:
    name: str
    description: Optional[str]
    arguments: Dict[str, CommandArgumentHelpData]


@dataclasses.dataclass
class CommandData:
    function: Callable
    name: str
    parse: Optional[pydantic.BaseModel]
    help_data: Optional[CommandHelpData]


@dataclasses.dataclass
class CustomLoaderData:
    callback: Callable
