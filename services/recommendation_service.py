from services.query_analyzer import QueryAnalyzer, QueryType, AnalysisResult
from services.tmdb_service import TMDBClient
from services.ollama_service import OllamaService
from services.recommendation_result import RecommendationResult


class RecommendationService:
    """Orchestrates movie recommendations using query analysis and TMDB data."""

    def __init__(self, analyzer: QueryAnalyzer, tmdb: TMDBClient, ollama: OllamaService) -> None:
        self.analyzer = analyzer
        self.tmdb = tmdb
        self.ollama = ollama

    def recommend(self, user_query: str) -> RecommendationResult:
        """Process a user query and return a recommendation result.

        Args:
            user_query: Raw text from the user.

        Returns:
            A RecommendationResult with the outcome.
        """
        result: AnalysisResult = self.analyzer.analyze(user_query)

        if result.query_type == QueryType.SIMILAR_MOVIE:
            return self._handle_similar_movie(user_query, result.value)

        if result.query_type == QueryType.PERSON:
            return self._handle_person(result.value)

        if result.query_type == QueryType.GENRE:
            return self._handle_genre(result.value)

        return self._handle_ai_required(user_query)

    def _handle_similar_movie(self, user_query: str, movie_title: str | None) -> RecommendationResult:
        """Find movies similar to a given title using TMDB and Ollama."""
        if not movie_title:
            return RecommendationResult(
                success=False,
                message="Укажите название фильма.",
                movies=[],
            )

        movie = self.tmdb.search_movie(movie_title)
        if not movie:
            return RecommendationResult(
                success=False,
                message="Фильм не найден.",
                movies=[],
            )

        similar = self.tmdb.get_similar_movies(movie["id"])
        if not similar:
            return RecommendationResult(
                success=False,
                message="Похожие фильмы не найдены.",
                movies=[],
            )

        similar = similar[:5]
        response = self.ollama.generate_recommendation(user_query, similar)
        return RecommendationResult(
            success=True,
            message=response,
            movies=similar,
        )

    def _handle_person(self, value: str | None) -> RecommendationResult:
        """Handle a request for movies by a specific person."""
        return RecommendationResult(
            success=False,
            message="PERSON — TODO",
            movies=[],
        )

    def _handle_genre(self, value: str | None) -> RecommendationResult:
        """Handle a request for movies of a specific genre."""
        return RecommendationResult(
            success=False,
            message="GENRE — TODO",
            movies=[],
        )

    def _handle_ai_required(self, user_query: str) -> RecommendationResult:
        """Handle a complex request that requires AI processing."""
        return RecommendationResult(
            success=False,
            message="AI_REQUIRED — TODO",
            movies=[],
        )