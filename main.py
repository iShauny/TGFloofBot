from telegram.ext import Updater, InlineQueryHandler, CommandHandler
from services import bot_init


def main():
    InitialiseBot = bot_init.BotInit()
    updater = InitialiseBot.get_updater()
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()