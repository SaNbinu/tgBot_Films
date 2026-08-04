import ollama
from typing import Any


SYSTEM_PROMPT: str = (
    "Ты опытный киноэксперт. Отвечай только на русском языке.\n\n"
    "Фильмы уже выбраны. Твоя задача — объяснить, почему каждый подходит. "
    "Не придумывай фильмы. Не меняй порядок. Не пропускай фильмы. "
    "Не пиши вступление и заключение.\n\n"
    "Для каждого фильма выведи:\n"
    "1. Название (год)\n"
    "⭐ рейтинг TMDB\n\n"
    "2–3 предложения с объяснением.\n"
)


NORMALIZER_SYSTEM_PROMPT: str = (
    "Ты нормализатор названий фильмов.\n"
    "Твоя задача — преобразовать пользовательский запрос к каноническому названию фильма.\n\n"
    "Правила:\n"
    "1. Не переводи язык.\n"
    "2. Не добавляй ничего лишнего.\n"
    "3. Верни только официальное название фильма в именительном падеже.\n"
    "4. Если запрос уже является названием фильма — верни его без изменений.\n"
)


class OllamaService:
    """Client for interacting with a local Ollama instance."""

    def __init__(self, model: str = "qwen2.5:7b", host: str = "http://localhost:11434") -> None:
        self.model: str = model
        self.host: str = host
        self.client = ollama.Client(host=self.host)

    def rerank_movies(self, user_query: str, movies: list[dict], source_movie: dict | None = None) -> list[str]:
        """Ask Ollama to select the 3 best-matching movies from a candidate list.

        Args:
            user_query: The user's original request.
            movies: A list of up to 10 candidate movie dicts from TMDB.
            source_movie: The original source movie dict (for comparison context).

        Returns:
            A list of up to 3 movie titles selected by the model.
        """
        source_title = (source_movie or {}).get("title", "Неизвестный фильм")

        candidate_lines = "\n".join(
            f"{i}. «{m.get('title', '?')}» ({m.get('release_date', '')[:4]})"
            for i, m in enumerate(movies, 1)
        )

        prompt = (
            "Ты профессиональный кинокритик.\n\n"
            "Тебе дан исходный фильм и список фильмов-кандидатов.\n\n"
            "Твоя задача — выбрать ТОЛЬКО 3 фильма, которые максимально похожи по СМЫСЛУ.\n\n"
            "Приоритет оценки (от самого важного к менее важному):\n\n"
            "1. Центральная идея фильма.\n"
            "2. Главная тема.\n"
            "3. Концепция мира.\n"
            "4. Атмосфера.\n"
            "5. Тип повествования.\n"
            "6. Эмоции после просмотра.\n"
            "7. Тип конфликта.\n"
            "8. Только потом жанр.\n\n"
            "НЕ выбирай фильм только потому что:\n\n"
            "- совпадает жанр;\n"
            "- есть искусственный интеллект;\n"
            "- есть космос;\n"
            "- есть мафия;\n"
            "- есть супергерои;\n"
            "- фильм очень популярный.\n\n"
            "Если есть фильм менее популярный, но намного ближе по смыслу — выбирай именно его.\n\n"
            "Представь, что пользователь после просмотра исходного фильма сказал:\n\n"
            "\"Хочу испытать похожие ощущения.\"\n\n"
            "Именно это должно определять выбор.\n\n"
            "Ответь только тремя названиями.\n"
            "Без номеров.\n"
            "Без пояснений.\n"
            "Без дополнительных слов.\n"
            "Каждое название с новой строки.\n\n"
            f"Исходный фильм:\n{source_title}\n\n"
            f"Кандидаты:\n{candidate_lines}"
        )

        print("=== OLLAMA PROMPT ===")
        print(prompt)
        print("=== END PROMPT ===")

        response = self._query_model(prompt)
        print("=== OLLAMA RAW RESPONSE ===")
        print(response)
        print("=== END RAW RESPONSE ===")

        titles = [
            line.strip().strip('"').strip("«").strip("»").strip("'")
            for line in response.strip().split("\n")
            if line.strip()
        ]
        print(f"Ollama rerank response:\n{response}")
        print(f"Parsed titles: {titles}")
        return titles[:3]

    def normalize_movie_title(self, query: str) -> str:
        """Normalize a user query to the canonical movie title in nominative case.

        Args:
            query: A raw user query that may contain a movie title in any
                grammatical case.

        Returns:
            The canonical movie title, or the original query if the model
            returned an empty response.
        """
        prompt = (
            "Преобразуй пользовательский запрос к каноническому названию фильма.\n"
            "Не переводи язык.\n"
            "Не добавляй ничего.\n"
            "Верни только официальное название фильма в именительном падеже.\n\n"
            "Примеры:\n"
            "матрицу -> Матрица\n"
            "начала -> Начало\n"
            "интерстеллара -> Интерстеллар\n"
            "крестного отца -> Крёстный отец\n\n"
            f"Запрос: {query}\n"
        )

        print("=== OLLAMA NORMALIZER PROMPT ===")
        print(prompt)
        print("=== END PROMPT ===")

        response = self._query_model(prompt, system_prompt=NORMALIZER_SYSTEM_PROMPT)
        print("=== OLLAMA NORMALIZER RESPONSE ===")
        print(response)
        print("=== END RESPONSE ===")

        title = response.replace('"', "").replace("«", "").replace("»", "").replace("'", "")
        title = " ".join(title.split())
        return title or query

    def generate_recommendation(self, user_query: str, movies: list[dict]) -> str:
        """Generate a recommendation based on user query and TMDB movie data.

        Args:
            user_query: The user's original request.
            movies: A list of movie dicts from TMDB.

        Returns:
            A formatted recommendation string from the model.
        """
        movies_text = self._format_movies(movies)
        prompt = (
            f"Запрос пользователя: {user_query}\n\n"
            f"Вот реальные фильмы из базы данных:\n{movies_text}\n\n"
            "Дай рекомендацию на основе этих фильмов. "
            "Не выдумывай фильмы, которых нет в списке."
        )
        return self._query_model(prompt)

    def generate_response(self, user_query: str) -> str:
        """Send a free-form user query directly to the model.

        Args:
            user_query: The user's raw text.

        Returns:
            The model's response text.
        """
        return self._query_model(user_query)

    def _format_movies(self, movies: list[dict]) -> str:
        """Convert a list of movie dicts into a readable text block."""
        lines: list[str] = []
        for i, m in enumerate(movies[:3], 1):
            title = m.get("title", "Unknown")
            year = m.get("release_date", "")[:4] if m.get("release_date") else "N/A"
            rating = m.get("vote_average", "N/A")
            overview = m.get("overview")
            if overview:
                if len(overview) > 190:
                    overview = overview[:190].rsplit(" ", 1)[0] + "..."
            else:
                overview = "Описание отсутствует"
            lines.append(f"{i}. {title} ({year}) — рейтинг: {rating}\n   {overview}")
        return "\n\n".join(lines)

    def _query_model(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
        """Send a prompt to Ollama and return the response text."""
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            return response["message"]["content"]
        except Exception as e:
            raise ConnectionError(f"Ollama request failed: {e}") from e
