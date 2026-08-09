from bot import bot

HELP_TEXT = (
    "📚 MovieScorer Help\n\n"
    "🎬 /movie <title>\n"
    "Get detailed information about a movie.\n"
    "Example: /movie Interstellar\n\n"
    "🔎 Recommendations\n"
    "Get personalized movie recommendations.\n\n"
    "📋 Watched\n"
    "View and manage movies you've watched.\n\n"
    "❤️ Wanted\n"
    "View and manage movies you want to watch.\n\n"
    "⬅️ Back\n"
    "Return to the main menu.\n\n"
    "💡 Tip: You can use /start at any time to return to the main menu."
)


@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(message.chat.id, HELP_TEXT)