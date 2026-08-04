from bot import bot
from keyboards.menus import films_menu, watched_menu, wanted_menu
from services.db import add_film, get_films
from services.query_analyzer import QueryAnalyzer
from services.tmdb_service import TMDBClient
from services.ollama_service import OllamaService
from services.recommendation_service import RecommendationService
from datetime import datetime

analyzer = QueryAnalyzer()
tmdb = TMDBClient()
ollama = OllamaService()

recommendation_service = RecommendationService(
    analyzer,
    tmdb,
    ollama,
)

#user_state = {}
state = {}



# ================================================================
# FORMAT OUTPUT
# ================================================================

def format_films(rows):
    if not rows:
        return "Список пуст"

    text = ""
    for i, item in enumerate(rows):
        text += f"{i}. {item[0]} | {item[1]}\n"
    return text


# ================================================================
# ADD LOGIC
# ================================================================

def process_add(message):
    current = state.get(message.chat.id)

    if current == "add_watched":
        add_film(message.chat.id, message.text, "watched")
        data = get_films(message.chat.id, "watched")

    elif current == "add_wanted":
        add_film(message.chat.id, message.text, "wanted")
        data = get_films(message.chat.id, "wanted")

    else:
        bot.send_message(message.chat.id, "Error state")
        return

    bot.send_message(message.chat.id, "Added")
    bot.send_message(
        message.chat.id,
        format_films(data),
        reply_markup=films_menu()
    )

    state[message.chat.id] = "main"


# ================================================================
# HANDLER
# ================================================================

@bot.message_handler(func=lambda m: True)
def handler(message):
    current = state.get(message.chat.id)
    text = message.text.lower()

    # ---------------- FSM: ADD ----------------
    if current in ("add_watched", "add_wanted"):
        process_add(message)
        return

    # ---------------- FSM: RECOMMEND ----------------
    if current == "recommend":
        _handle_recommend(message)
        return

    # ---------------- MAIN MENU ----------------
    if text == "films":
        bot.send_message(message.chat.id, "Choose option", reply_markup=films_menu())

    # ---------------- WATCHED ----------------
    elif text == "смотрел":
        state[message.chat.id] = "watched"

        data = get_films(message.chat.id, "watched")

        bot.send_message(
            message.chat.id,
            format_films(data),
            reply_markup=watched_menu()
        )

    # ---------------- WANTED ----------------
    elif text == "желание":
        state[message.chat.id] = "wanted"

        data = get_films(message.chat.id, "wanted")

        bot.send_message(
            message.chat.id,
            format_films(data),
            reply_markup=wanted_menu()
        )

    # ---------------- ADD ----------------
    elif text == "add":
        if current == "watched":
            state[message.chat.id] = "add_watched"
        elif current == "wanted":
            state[message.chat.id] = "add_wanted"
        else:
            state[message.chat.id] = "add_watched"

        bot.send_message(message.chat.id, "Enter film name")

    #------------------BACK----------------
    elif text == "back":
        state[message.chat.id] = "main"
        bot.send_message(
            message.chat.id,
            "Main menu",
            reply_markup=films_menu()
        )

    # ---------------- RECOMMEND ----------------
    elif text == "рекомендация":
        state[message.chat.id] = "recommend"
        bot.send_message(message.chat.id, "What do you want?")


def _handle_recommend(m):
    print("START recommendation")
    result = recommendation_service.recommend(m.text)
    print("Recommendation ready")
    bot.send_message(m.chat.id, result.message)
    state[m.chat.id] = "main"
    print("Message sent")