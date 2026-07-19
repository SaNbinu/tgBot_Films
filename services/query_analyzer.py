import re
from enum import Enum
from dataclasses import dataclass


class QueryType(Enum):
    SIMILAR_MOVIE = "similar_movie"
    PERSON = "person"
    GENRE = "genre"
    DISCOVER = "discover"
    AI_REQUIRED = "ai_required"


@dataclass
class AnalysisResult:
    query_type: QueryType
    value: str | None = None
    needs_ai: bool = False


GENRE_KEYWORDS: dict[str, str] = {
    "комедия": "comedy",
    "комедии": "comedy",
    "комедию": "comedy",
    "комедийный": "comedy",
    "ужасы": "horror",
    "ужастик": "horror",
    "ужастики": "horror",
    "боевик": "action",
    "боевики": "action",
    "фантастика": "sci-fi",
    "фантастику": "sci-fi",
    "фантастический": "sci-fi",
    "драма": "drama",
    "драмы": "drama",
    "триллер": "thriller",
    "триллеры": "thriller",
    "мелодрама": "romance",
    "мелодрамы": "romance",
    "детектив": "mystery",
    "детективы": "mystery",
    "приключения": "adventure",
    "приключенческий": "adventure",
    "мультфильм": "animation",
    "мультик": "animation",
    "мульт": "animation",
    "фэнтези": "fantasy",
    "вестерн": "western",
    "документальный": "documentary",
    "исторический": "history",
    "военный": "war",
    "музыкальный": "music",
    "криминал": "crime",
    "криминальный": "crime",
    "семейный": "family",
}

PATTERNS: list[tuple[re.Pattern, QueryType, str | None]] = [
    (re.compile(r"похожее?\s+на\s+(.+)", re.IGNORECASE), QueryType.SIMILAR_MOVIE, None),
    (re.compile(r"фильмы?\s+с\s+(.+)", re.IGNORECASE), QueryType.PERSON, None),
    (re.compile(r"фильмы?\s+(.+)", re.IGNORECASE), QueryType.PERSON, None),
]


class QueryAnalyzer:
    """Analyzes user text and determines the type of movie query."""

    def analyze(self, text: str) -> AnalysisResult:
        """Determine the query type from user input.

        Args:
            text: Raw user message.

        Returns:
            An AnalysisResult with the detected query type, extracted value,
            and whether AI processing is needed.
        """
        cleaned = text.strip().lower()

        for pattern, query_type, _ in PATTERNS:
            match = pattern.search(cleaned)
            if match:
                value = match.group(1).strip()
                return AnalysisResult(
                    query_type=query_type,
                    value=value,
                    needs_ai=False,
                )

        for genre_name in GENRE_KEYWORDS:
            if genre_name in cleaned:
                return AnalysisResult(
                    query_type=QueryType.GENRE,
                    value=genre_name,
                    needs_ai=False,
                )

        return AnalysisResult(
            query_type=QueryType.AI_REQUIRED,
            value=None,
            needs_ai=True,
        )
