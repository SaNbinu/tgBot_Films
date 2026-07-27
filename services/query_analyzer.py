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
    "ужасов": "horror",
    "ужастик": "horror",
    "ужастики": "horror",
    "ужастиков": "horror",
    "боевик": "action",
    "боевики": "action",
    "боевика": "action",
    "боевиков": "action",
    "фантастика": "sci-fi",
    "фантастику": "sci-fi",
    "фантастический": "sci-fi",
    "фантастические": "sci-fi",
    "фантастических": "sci-fi",
    "драма": "drama",
    "драмы": "drama",
    "драму": "drama",
    "триллер": "thriller",
    "триллеры": "thriller",
    "триллера": "thriller",
    "триллеров": "thriller",
    "мелодрама": "romance",
    "мелодрамы": "romance",
    "мелодраму": "romance",
    "детектив": "mystery",
    "детективы": "mystery",
    "детектива": "mystery",
    "детективов": "mystery",
    "детективный": "mystery",
    "приключения": "adventure",
    "приключенческий": "adventure",
    "приключенческие": "adventure",
    "приключенческих": "adventure",
    "мультфильм": "animation",
    "мультфильмы": "animation",
    "мультфильмов": "animation",
    "мультик": "animation",
    "мультики": "animation",
    "мультиков": "animation",
    "мульт": "animation",
    "аниме": "animation",
    "фэнтези": "fantasy",
    "вестерн": "western",
    "вестерны": "western",
    "документальный": "documentary",
    "исторический": "history",
    "военный": "war",
    "военные": "war",
    "военных": "war",
    "музыкальный": "music",
    "криминал": "crime",
    "криминальный": "crime",
    "криминала": "crime",
    "семейный": "family",
    "семейные": "family",
    "семейных": "family",
}

THEME_TO_GENRE: dict[str, str] = {
    "космос": "фантастика",
    "войну": "военный",
    "зомби": "ужасы",
    "вампиров": "ужасы",
}

FILMY_PRO_PATTERN: re.Pattern = re.compile(
    r"фильмы?\s+про\s+(.+)",
    re.IGNORECASE,
)

SIMILAR_PATTERNS: list[tuple[re.Pattern, QueryType, str | None]] = [
    (re.compile(
        r"(?:.*?)(?:похож(?:ее|ий|ие|ая|их|им|ими|его|ему|им|ую|ей|его|ему)?)\s+на\s+(.+)",
        re.IGNORECASE,
    ), QueryType.SIMILAR_MOVIE, None),
]

PERSON_PATTERNS: list[tuple[re.Pattern, QueryType, str | None]] = [
    (re.compile(r"фильмы?\s+с\s+(.+)", re.IGNORECASE), QueryType.PERSON, None),
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
