# 🎬 MovieScorer

A Telegram bot for discovering movies, managing watchlists, and getting personalized recommendations.

MovieScorer combines the TMDB API for real movie data with a local Ollama LLM for recommendation re-ranking and explanations.

## ✨ Features

- `/start` — welcome message and main menu
- `/help` — available commands
- `/movie <title>` — detailed movie information
- `/movie <tmdb_id>` — search by TMDB ID
- Smart movie title matching
- Watched and Wanted lists
- TMDB-validated movie adding
- Duplicate protection
- Movie deletion
- Natural-language recommendations
- Content-based movie scoring
- Ollama-powered recommendation re-ranking and explanations

## 🛠️ Tech Stack

- Python 3.12+
- pyTelegramBotAPI
- SQLite
- TMDB API v3
- Ollama + Qwen 2.5 7B
- requests
- python-dotenv
- pymorphy3

## 🧩 Architecture

The project follows a simple layered architecture:

    Telegram
        │
        ▼
    Handlers
        │
        ▼
    Services
     ┌──┼──────────────┐
     ▼  ▼              ▼
    TMDB SQLite      Ollama
     │                 │
     └───────┬─────────┘
             ▼
          Response

### Main components

- `handlers/` — Telegram commands, menus and state management
- `services/tmdb_service.py` — TMDB API client
- `services/title_matcher.py` — movie title matching
- `services/movie_scorer.py` — content-based candidate scoring
- `services/query_analyzer.py` — recommendation query analysis
- `services/recommendation_service.py` — recommendation orchestration
- `services/ollama_service.py` — local LLM integration
- `services/db.py` — SQLite persistence
- `keyboards/` — Telegram keyboards

## 📁 Project Structure

    MovieScorer/
    ├── bot.py
    ├── config.py
    ├── main.py
    ├── requirements.txt
    ├── .env.example
    ├── .gitignore
    │
    ├── handlers/
    │   ├── films.py
    │   ├── help.py
    │   ├── movie.py
    │   └── start.py
    │
    ├── keyboards/
    │   └── menus.py
    │
    └── services/
        ├── db.py
        ├── movie_scorer.py
        ├── ollama_service.py
        ├── query_analyzer.py
        ├── recommendation_result.py
        ├── recommendation_service.py
        ├── title_matcher.py
        └── tmdb_service.py

## 🚀 Setup

### Requirements

- Python 3.12+
- Telegram bot token
- TMDB API key
- Ollama with `qwen2.5:7b`

### Installation

    git clone https://github.com/SaNbinu/MovieScorer.git
    cd MovieScorer

    python -m venv venv
    venv\Scripts\activate
    # source venv/bin/activate  # macOS / Linux

    pip install -r requirements.txt

Create a `.env` file:

    TOKEN=your_telegram_bot_token
    TMDB_API_KEY=your_tmdb_api_key

Install the Ollama model:

    ollama pull qwen2.5:7b

Run the bot:

    python main.py

The bot uses long polling, so no webhook setup is required.