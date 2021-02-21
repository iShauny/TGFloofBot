from telegram.ext import Updater, InlineQueryHandler, CommandHandler
from services.decorators import command


class Utilities():
    def __init__(self, bot, update):
        self.name = "Utilities"

    def get_module_name(self):
        return self.name

    @command
    def pong(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="Pong!")
