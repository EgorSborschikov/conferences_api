from os import getenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def run_telegram_bot():

    updater = Updater(getenv("API_TOKEN_BOT"))
    dispatcher = updater.dispatcher

    def start(update: Update, context: CallbackContext) -> None:
        logger.info("Команда /start получена")
        update.message.reply_text('Привет! Я бот-помощник. Что бы вы хотели узнать?')

    def help_command(update: Update, context: CallbackContext) -> None:
        help_text = (
            "Если в приложении что-то не работает, попробуйте следующие шаги:\n"
            "1. Убедитесь, что у вас есть подключение к интернету.\n"
            "2. Перезапустите приложение.\n"
            "3. Убедитесь, что у вас установлена последняя версия приложения.\n"
            "4. Проверьте настройки приложения.\n"
            "5. Если проблема сохраняется, обратитесь в службу поддержки."
        )
        update.message.reply_text(help_text)

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    logger.info("Запуск бота...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    run_telegram_bot()