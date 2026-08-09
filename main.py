import logging
import handlers.movie
import handlers.start
import handlers.help
import handlers.films
from bot import bot
from services.db import init_db

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    init_db()
    logger = logging.getLogger(__name__)
    logger.info("Bot started")
    bot.polling()

if __name__ == "__main__":
    main()