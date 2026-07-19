from services.query_analyzer import QueryAnalyzer, QueryType, AnalysisResult
from services.tmdb_service import TMDBClient


class RecommendationService:
    """Orchestrates movie recommendations using query analysis and TMDB data."""

    def __init__(self, analyzer: QueryAnalyzer, tmdb: TMDBClient) -> None:
        self.analyzer = analyzer
        self.tmdb = tmdb

    def recommend(self, user_query: str) -> str:
        """Process a user query and return a recommendation response.

        Args:
            user_query: Raw text from the user.

        Returns:
            A string response with the recommendation result.
        """
        result: AnalysisResult = self.analyzer.analyze(user_query)

        if result.query_type == QueryType.SIMILAR_MOVIE:
            return self._handle_similar_movie(result.value)

        if result.query_type == QueryType.PERSON:
            return self._handle_person(result.value)

        if result.query_type == QueryType.GENRE:
            return self._handle_genre(result.value)

        return self._handle_ai_required(user_query)

    def _handle_similar_movie(self, value: str | None) -> str:
        """Handle a request for movies similar to a given title."""
        return "SIMILAR_MOVIE"

    def _handle_person(self, value: str | None) -> str:
        """Handle a request for movies by a specific person."""
        return "PERSON"

    def _handle_genre(self, value: str | None) -> str:
        """Handle a request for movies of a specific genre."""
        return "GENRE"

    def _handle_ai_required(self, user_query: str) -> str:
        """Handle a complex request that requires AI processing."""
        return "AI_REQUIRED"