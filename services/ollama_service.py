import ollama
from typing import Any


SYSTEM_PROMPT: str = (
    "You are an experienced film expert. Respond only in English.\n\n"
    "Movies have already been selected. Your task is to explain why each one fits. "
    "Don't invent movies. Don't change the order. Don't skip movies. "
    "Don't write an introduction or a conclusion.\n\n"
    "For each movie provide:\n"
    "1. Title (year)\n"
    "⭐ TMDB rating\n\n"
    "2-3 sentences with an explanation.\n"
)


NORMALIZER_SYSTEM_PROMPT: str = (
    "You are a movie title normalizer.\n"
    "Your task is to convert a user query into the canonical movie title.\n\n"
    "Rules:\n"
    "1. Do not translate the language.\n"
    "2. Don't add anything extra.\n"
    "3. Return only the official movie title.\n"
    "4. If the query is already a movie title — return it unchanged.\n"
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
        source_title = (source_movie or {}).get("title", "Unknown movie")

        candidate_lines = "\n".join(
            f"{i}. «{m.get('title', '?')}» ({m.get('release_date', '')[:4]})"
            for i, m in enumerate(movies, 1)
        )

        prompt = (
            "You are a professional film critic.\n\n"
            "You are given a source movie and a list of candidate movies.\n\n"
            "Your task is to choose ONLY 3 movies that are the most similar in MEANING.\n\n"
            "Priority of evaluation (from most to least important):\n\n"
            "1. The central idea of the movie.\n"
            "2. The main theme.\n"
            "3. The world concept.\n"
            "4. The atmosphere.\n"
            "5. The type of storytelling.\n"
            "6. The emotions after watching.\n"
            "7. The type of conflict.\n"
            "8. Only then genre.\n\n"
            "Do NOT choose a movie just because:\n\n"
            "- the genre matches;\n"
            "- it features artificial intelligence;\n"
            "- it features space;\n"
            "- it features mafia;\n"
            "- it features superheroes;\n"
            "- the movie is very popular.\n\n"
            "If there is a less popular movie but much closer in meaning — choose it.\n\n"
            "Imagine that the user said after watching the source movie:\n\n"
            "\"I want to feel something similar.\"\n\n"
            "That should determine your choice.\n\n"
            "Answer with only three titles.\n"
            "No numbers.\n"
            "No explanations.\n"
            "No extra words.\n"
            "One title per line.\n\n"
            f"Source movie:\n{source_title}\n\n"
            f"Candidates:\n{candidate_lines}"
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
            "Convert the user query to the canonical movie title.\n"
            "Do not translate the language.\n"
            "Do not add anything.\n"
            "Return only the official movie title.\n\n"
            "Examples:\n"
            "godfather -> The Godfather\n"
            "dark knight -> The Dark Knight\n"
            "harry potter -> Harry Potter and the Philosopher's Stone\n"
            "green mile -> The Green Mile\n\n"
            f"Query: {query}\n"
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
            f"User query: {user_query}\n\n"
            f"Here are the real movies from the database:\n{movies_text}\n\n"
            "Give a recommendation based on these movies. "
            "Do not invent movies that are not in the list."
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
                overview = "No description available"
            lines.append(f"{i}. {title} ({year}) — rating: {rating}\n   {overview}")
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
