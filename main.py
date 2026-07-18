import handlers.start
import handlers.films
from bot import bot
from services.db import init_db

def main():
    init_db()
    print("Bot started")
    bot.polling()

if __name__ == "__main__":
    main()