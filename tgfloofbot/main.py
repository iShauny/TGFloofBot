import argparse
import logging
import pathlib
import sys

import yaml

from sqlalchemy.sql.schema import MetaData

from . import client
from . import constants
from . import models

from .logger import LOG


def start(config: models.Config) -> int:

    ## Setup logging
    stream_log_handler = LOG.handlers[0]
    if config.debug:
        stream_log_handler.setLevel(logging.DEBUG)
    rotating_log_handler = logging.handlers.RotatingFileHandler(
        **dict(config.log), encoding="utf-8"
    )
    rotating_log_handler.setLevel(logging.DEBUG)
    rotating_log_handler.setFormatter(stream_log_handler.formatter)
    LOG.addHandler(rotating_log_handler)

    ## Create bot client instance
    bot_client = client.TGFloofbotClient(config)
    bot_client.run()
    return 0


def cli_start() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=pathlib.Path,
        default="config.yaml",
        help="Path of the config file",
    )
    parsed = parser.parse_args()
    try:
        raw_config = yaml.safe_load(parsed.config.read_text())
        config = models.Config(**raw_config)
    except Exception as err:
        LOG.exception("Config file cannot loaded:")
        sys.exit(1)
    sys.exit(start(config))


def load_db_metadata() -> MetaData:
    """Helper function for loading DB models and returning the """
    from . import plugins

    return models.ORMBase.metadata
