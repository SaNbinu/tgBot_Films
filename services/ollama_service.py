import ollama
from typing import Any


SYSTEM_PROMPT: str = (
    "Ты профессиональный киноэксперт. Отвечай на русском языке. "
    "Используй только те фильмы, которые тебе предоставили. "
    "Не выдумывай названия, годы, рейтинги или актёров. "
    "Для каждого фильма укажи: название, год, краткое описание и рейтинг."
)


class OllamaService:
    """Client for interacting with a local Ollama instance."""

    def __init__(self, model: str = "qwen3:8b", host: str = "http://localhost:11434") -> None:
        self.model: str = model
        self.host: str = host
        self.client = ollama.Client(host=self.host)

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
        for i, m in enumerate(movies, 1):
            title = m.get("title", "Unknown")
            year = m.get("release_date", "")[:4] if m.get("release_date") else "N/A"
            rating = m.get("vote_average", "N/A")
            overview = m.get("overview", "No description")
            lines.append(f"{i}. {title} ({year}) — рейтинг: {rating}\n   {overview}")
        return "\n\n".join(lines)

    def _query_model(self, prompt: str) -> str:
        """Send a prompt to Ollama and return the response text."""
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            return response["message"]["content"]
        except Exception as e:
            raise ConnectionError(f"Ollama request failed: {e}") from e
