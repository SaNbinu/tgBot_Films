from bot import bot
from services.tmdb_service import TMDBClient

tmdb = TMDBClient()

_LANGUAGE_NAMES = {
    "ar": "Arabic", "cs": "Czech", "da": "Danish", "de": "German",
    "en": "English", "es": "Spanish", "fi": "Finnish", "fr": "French",
    "he": "Hebrew", "hi": "Hindi", "hu": "Hungarian", "id": "Indonesian",
    "it": "Italian", "ja": "Japanese", "ko": "Korean", "nl": "Dutch",
    "no": "Norwegian", "pl": "Polish", "pt": "Portuguese", "ru": "Russian",
    "sv": "Swedish", "th": "Thai", "tr": "Turkish", "uk": "Ukrainian",
    "vi": "Vietnamese", "zh": "Chinese",
}


def _format_movie(details: dict, people: dict) -> str:
    title = details.get("title", "Unknown movie")
    year = (details.get("release_date") or "")[:4]
    if year:
        title = f"{title} ({year})"

    blocks = [f"🎬 {title}"]

    rating = details.get("vote_average")
    if rating is not None:
        votes = f"{details.get('vote_count', 0):,}"
        blocks.append(f"⭐ TMDB: {rating:.1f} ({votes} votes)")

    genres = ", ".join(g.get("name", "") for g in details.get("genres", []))
    if genres:
        blocks.append(f"🎭 Genres:\n{genres}")

    director = people.get("director")
    if director:
        blocks.append(f"🎬 Director:\n{director}")

    cast = people.get("cast", [])
    if cast:
        blocks.append(f"🎭 Cast:\n{', '.join(cast)}")

    countries = ", ".join(
        c.get("name", "") for c in details.get("production_countries", [])
    )
    if countries:
        blocks.append(f"🌍 Country:\n{countries}")

    language = details.get("original_language")
    if language:
        name = _LANGUAGE_NAMES.get(language, language.upper())
        blocks.append(f"🗣 Original language:\n{name}")

    runtime = details.get("runtime")
    if runtime:
        blocks.append(f"⏱ Runtime:\n{runtime} min")

    tagline = details.get("tagline")
    if tagline:
        blocks.append(f"💬 Tagline:\n{tagline}")

    overview = details.get("overview")
    if overview:
        blocks.append(f"📝 Overview:\n{overview}")

    return "\n\n".join(blocks)


@bot.message_handler(commands=["movie"])
def handle_movie(message):
    arg = ""
    if message.text and len(message.text.split(" ", 1)) > 1:
        arg = message.text.split(" ", 1)[1].strip()

    if not arg:
        bot.send_message(
            message.chat.id,
            "Usage: /movie <title or TMDB id>",
        )
        return

    if arg.isdigit():
        movie_id = int(arg)
        details = tmdb.get_movie_details(movie_id)
        if not details:
            bot.send_message(message.chat.id, "Movie not found.")
            return
    else:
        movie = tmdb.search_movie(arg)
        if not movie:
            bot.send_message(message.chat.id, "Movie not found.")
            return
        details = tmdb.get_movie_details(movie["id"])
        if not details:
            bot.send_message(message.chat.id, "Movie not found.")
            return

    people = tmdb.get_movie_people(details["id"])
    text = _format_movie(details, people)

    poster = tmdb.get_poster_url(details.get("poster_path"))
    if poster:
        try:
            if len(text) > 1024:
                text = text[:1021] + "..."
            bot.send_photo(message.chat.id, poster, caption=text)
        except Exception:
            bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, text)