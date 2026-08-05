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
    "comedy": "comedy",
    "comedies": "comedy",
    "horror": "horror",
    "horror movie": "horror",
    "horror movies": "horror",
    "scary": "horror",
    "action": "action",
    "action movie": "action",
    "action movies": "action",
    "sci-fi": "sci-fi",
    "scifi": "sci-fi",
    "science fiction": "sci-fi",
    "space": "sci-fi",
    "drama": "drama",
    "dramas": "drama",
    "thriller": "thriller",
    "thrillers": "thriller",
    "melodrama": "romance",
    "melodramas": "romance",
    "romance": "romance",
    "romantic": "romance",
    "mystery": "mystery",
    "mysteries": "mystery",
    "detective": "mystery",
    "detectives": "mystery",
    "adventure": "adventure",
    "adventures": "adventure",
    "cartoon": "animation",
    "cartoons": "animation",
    "animated": "animation",
    "animation": "animation",
    "anime": "animation",
    "fantasy": "fantasy",
    "western": "western",
    "westerns": "western",
    "documentary": "documentary",
    "documentaries": "documentary",
    "historical": "history",
    "history": "history",
    "war": "war",
    "wars": "war",
    "war movie": "war",
    "war movies": "war",
    "musical": "music",
    "musicals": "music",
    "crime": "crime",
    "criminal": "crime",
    "family": "family",
    "family movie": "family",
}

THEME_TO_GENRE: dict[str, str] = {
    "space": "sci-fi",
    "war": "war",
    "zombie": "horror",
    "zombies": "horror",
    "vampire": "horror",
    "vampires": "horror",
}

FILMY_PRO_PATTERN: re.Pattern = re.compile(
    r"movies?\s+about\s+(.+)",
    re.IGNORECASE,
)

SIMILAR_PATTERNS: list[tuple[re.Pattern, QueryType, str | None]] = [
    (re.compile(
        r"(?:.*?)(?:similar\s+to|movies?\s+like|films?\s+like|something\s+like|anything\s+like)\s+(.+)$",
        re.IGNORECASE,
    ), QueryType.SIMILAR_MOVIE, None),
]

PERSON_PATTERNS: list[tuple[re.Pattern, QueryType, str | None]] = [
    (re.compile(r"movies?\s+(?:with|by|starring)\s+(.+)", re.IGNORECASE), QueryType.PERSON, None),
    (re.compile(r"films?\s+(?:with|by|starring)\s+(.+)", re.IGNORECASE), QueryType.PERSON, None),
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
        print(f"INPUT: {text}")

        similar_with_prefix = SIMILAR_PATTERNS[0]
        match = similar_with_prefix[0].search(cleaned)
        if match:
            value = match.group(1).strip()
            print(f"QueryType={QueryType.SIMILAR_MOVIE}, value={value}")
            return AnalysisResult(
                query_type=QueryType.SIMILAR_MOVIE,
                value=value,
                needs_ai=False,
            )

        for genre_name in GENRE_KEYWORDS:
            if re.search(rf"\b{re.escape(genre_name)}\b", cleaned):
                print(f"QueryType={QueryType.GENRE}, value={genre_name}")
                return AnalysisResult(
                    query_type=QueryType.GENRE,
                    value=genre_name,
                    needs_ai=False,
                )

        theme_match = FILMY_PRO_PATTERN.search(cleaned)
        if theme_match:
            theme = theme_match.group(1).strip()
            if theme in THEME_TO_GENRE:
                print(f"QueryType={QueryType.GENRE}, value={theme}")
                return AnalysisResult(
                    query_type=QueryType.GENRE,
                    value=theme,
                    needs_ai=False,
                )

        for pattern, query_type, _ in PERSON_PATTERNS:
            match = pattern.search(cleaned)
            if match:
                value = match.group(1).strip()
                print(f"QueryType={query_type}, value={value}")
                return AnalysisResult(
                    query_type=query_type,
                    value=value,
                    needs_ai=False,
                )

        print(f"QueryType={QueryType.AI_REQUIRED}")
        return AnalysisResult(
            query_type=QueryType.AI_REQUIRED,
            value=cleaned,
            needs_ai=True,
        )
