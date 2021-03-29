import sys
import threading

from typing import Any, Callable, List, Optional

import sqlalchemy
import sqlalchemy.orm
import telegram
import telegram.ext

from . import models
from . import exceptions
from . import loader

from .helpers import em

from .logger import LOG


class TGFloofbotClient:
    def __init__(self, config: models.Config):
        self.config = config
        self.updater = telegram.ext.Updater(token=config.token)
        self.dispatcher = self.updater.dispatcher
        self.dispatcher.add_error_handler(self._handle_error)  # type: ignore
        self.connect_database()

        global global_client
        if global_client:
            raise ValueError("Only one bot client can be registered to the loader.")
        global_client = self
        LOG.debug("Client has assigned the global bot client")

        self.load_plugins()

    def _handle_error(
        self,
        update: telegram.update.Update,
        context: telegram.ext.callbackcontext.CallbackContext,
    ) -> None:
        try:
            if isinstance(context.error, exceptions.FloofbotSyntaxError):
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=str(context.error),
                    parse_mode=telegram.ParseMode.MARKDOWN_V2,
                )
            elif isinstance(context.error, exceptions.FloofbotException):
                if context.error.critical:
                    LOG.exception(
                        f"The bot is shutting down due to a critical exception: {context.error}"
                    )
                    self.stop()
                else:
                    LOG.error(context.error)
                if not context.error.silent:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"*{em(context.error.title)}:*\n{context.error}",
                        parse_mode=telegram.ParseMode.MARKDOWN_V2,
                    )
            else:
                if not str(context.error).startswith("Message is not modified:"):
                    LOG.exception("An unhandled exception was caught:")
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"*An unhandled exception occurred:*\n{em(context.error)}",
                        parse_mode=telegram.ParseMode.MARKDOWN_V2,
                    )
        except:
            LOG.exception("Error handler error:")

    def connect_database(self) -> None:
        LOG.debug("Connecting to database")
        self.engine = sqlalchemy.create_engine(
            f"sqlite:///{self.config.database.resolve()}", echo=True
        )

    def load_plugins(self) -> None:
        ## TODO: Make this load custom plugins from external directories
        from . import plugins

        LOG.debug("Bootstrapping database")
        models.ORMBase.metadata.create_all(self.engine)
        self.db = sqlalchemy.orm.sessionmaker(bind=self.engine)()

        for custom_loader in loader.custom_loaders:
            LOG.debug(f"Running custom loader: {custom_loader.__name__}")
            custom_loader(self)

    def run(self) -> None:
        LOG.debug("Starting the polling loop")
        self.updater.start_polling()
        self.updater.idle()
        LOG.debug("start_polling ended")

    def stop(self) -> None:
        LOG.info("The bot is now stopping")

        def _shutdown():
            self.updater.stop()
            self.updater.is_idle = False
            LOG.debug("Bot stopped")

        threading.Thread(target=_shutdown).start()


## Global variable for the client that will be used when registering commands and other handlers
global_client: Optional[TGFloofbotClient] = None
