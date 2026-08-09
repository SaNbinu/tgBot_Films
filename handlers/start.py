from bot import bot
from keyboards.menus import films_menu

@bot.message_handler(commands=["start"])
def start(message):
    from handlers.films import state

    state[message.chat.id] = "main"

    bot.send_message(
        message.chat.id,
        "🎬 Welcome to MovieScorer!\n\n"
        "Your personal movie companion.\n\n"
        "🔎 Find movies and get recommendations based on what you like.\n"
        "📋 Keep track of movies you've watched and want to watch.\n"
        "🎞️ Get detailed information about any movie.\n\n"
        "💡 Tip: Use /movie <title> to get detailed information about any movie.\n"
        "Use the buttons below to get started.",
        reply_markup=films_menu()
    )