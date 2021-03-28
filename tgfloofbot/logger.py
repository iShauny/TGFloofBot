import logging
import logging.config


logging.config.dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": (
                    "%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)s]: %(message)s"
                )
            }
        },
        "handlers": {
            "default": {
                "level": "INFO",
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "tgfb": {
                "handlers": ["default"],
                "level": "DEBUG",
                "propagate": False,
            },
        },
    }
)
LOG = logging.getLogger("tgfb")
