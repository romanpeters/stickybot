import locale
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import command
from redacted import BOT_TOKEN, KOALA_COOKIE

logger = logging.getLogger(__name__)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("agenda", command.agenda))
    dp.add_handler(CommandHandler("bier", command.bier))
    dp.add_handler(CommandHandler("stickers", command.stickers))

    # # on noncommand i.e message - echo the message on Telegram
    # dp.add_handler(MessageHandler(Filters.text, noncommand.echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    print("Listening...")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
