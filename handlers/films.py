from bot import bot
from keyboards.menus import films_menu, watched_menu, wanted_menu
from services.db import add_film, delete_movie, get_films
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
        return "List is empty"

    text = ""
    for i, item in enumerate(rows, 1):
        text += f"{i}. {item[0]} | {item[1][:10]}\n"
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
# DELETE LOGIC
# ================================================================

def process_delete(message):
    current = state.get(message.chat.id)

    if current == "delete_watched":
        status = "watched"
    elif current == "delete_wanted":
        status = "wanted"
    else:
        bot.send_message(message.chat.id, "Error state")
        return

    deleted = delete_movie(message.chat.id, message.text, status)
    data = get_films(message.chat.id, status)

    if deleted:
        bot.send_message(message.chat.id, "Deleted")
    else:
        bot.send_message(message.chat.id, "Movie not found in the list")

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

    # ---------------- BACK ----------------
    if text == "back":
        state[message.chat.id] = "main"
        bot.send_message(
            message.chat.id,
            "Main menu",
            reply_markup=films_menu()
        )
        return

    # ---------------- FSM: ADD ----------------
    if current in ("add_watched", "add_wanted"):
        process_add(message)
        return

    # ---------------- FSM: DELETE ----------------
    if current in ("delete_watched", "delete_wanted"):
        process_delete(message)
        return

    # ---------------- FSM: RECOMMEND ----------------
    if current == "recommend":
        _handle_recommend(message)
        return

    # ---------------- MAIN MENU ----------------
    if text == "films":
        bot.send_message(message.chat.id, "Choose option", reply_markup=films_menu())

    # ---------------- WATCHED ----------------
    elif text == "watched":
        state[message.chat.id] = "watched"

        data = get_films(message.chat.id, "watched")

        bot.send_message(
            message.chat.id,
            format_films(data),
            reply_markup=watched_menu()
        )

    # ---------------- WANTED ----------------
    elif text == "wanted":
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

    # ---------------- DELETE ----------------
    elif text == "delete movie":
        if current == "watched":
            state[message.chat.id] = "delete_watched"
        elif current == "wanted":
            state[message.chat.id] = "delete_wanted"
        else:
            state[message.chat.id] = "delete_watched"

        bot.send_message(message.chat.id, "Enter film name to delete")

    # ---------------- RECOMMEND ----------------
    elif text == "recommendation":
        state[message.chat.id] = "recommend"
        bot.send_message(message.chat.id, "What do you want?")


def _handle_recommend(m):
    print("START recommendation")
    result = recommendation_service.recommend(m.text)
    print("Recommendation ready")
    bot.send_message(m.chat.id, result.message)
    state[m.chat.id] = "main"
    print("Message sent")