import logging
import requests
import telebot
import telebot.apihelper as apihelper
from config import TOKEN

apihelper.RETRY_ON_ERROR = True
apihelper.MAX_RETRIES = 3
apihelper.RETRY_TIMEOUT = 3

logger = logging.getLogger(__name__)


class NetworkErrorHandler(telebot.ExceptionHandler):
    """Global exception handler: log the error and keep the bot alive
    for transient network errors."""

    def handle(self, exception) -> bool:
        logger.error(f"Telegram API error: {type(exception).__name__}: {exception}")
        if isinstance(
            exception,
            (requests.exceptions.RequestException, apihelper.ApiException, ConnectionResetError),
        ):
            return True
        return False


bot = telebot.TeleBot(TOKEN, exception_handler=NetworkErrorHandler())
