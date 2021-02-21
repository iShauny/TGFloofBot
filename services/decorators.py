from telegram.ext import Updater, InlineQueryHandler, CommandHandler


def command(cmd):
    def wrapper():
        super.dispatcher.add_handler(CommandHandler(cmd.__name__, cmd))

    return wrapper