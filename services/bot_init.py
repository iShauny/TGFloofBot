from telegram.ext import Updater, InlineQueryHandler, CommandHandler
from modules import *


class BotInit():
    def __init__(self):
        self.updater = Updater(
            '1610744003:AAE2bNZLg7tT0dOUCUWt0XCLS4c45q5BKLQ')
        self.dispatcher = self.updater.dispatcher

    def get_updater(self):
        return self.updater
