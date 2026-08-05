import math
import re
from typing import Any

WEIGHT_GENRES: float = 20.0
WEIGHT_KEYWORDS: float = 50.0
WEIGHT_OVERVIEW: float = 30.0
WEIGHT_YEAR: float = 10.0
WEIGHT_RATING: float = 8.0
WEIGHT_POPULARITY: float = 5.0
WEIGHT_BONUS: float = 8.0
WEIGHT_DIRECTOR: float = 15.0
WEIGHT_CAST: float = 10.0

MAX_YEAR_DIFF: int = 20
MAX_VOTE_COUNT: int = 100_000
RATING_THRESHOLD: float = 6.8
VOTE_COUNT_THRESHOLD: int = 1000
MIN_GENRE_OVERLAP: int = 2

STOP_WORDS: set[str] = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "is", "it", "as", "be", "are", "was", "were",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "not",
    "no", "nor", "so", "if", "then", "than", "that", "this", "these",
    "those", "i", "me", "my", "we", "our", "you", "your", "he", "him",
    "his", "she", "her", "they", "them", "their", "what", "which", "who",
    "whom", "when", "where", "why", "how", "all", "each", "every", "both",
    "few", "more", "most", "some", "any", "into", "over", "after", "before",
    "between", "through", "during", "about", "against", "under", "again",
    "further", "once", "here", "there", "up", "down", "out",
    "и", "в", "во", "на", "с", "со", "по", "для", "о", "об", "от",
    "из", "у", "к", "за", "не", "но", "а", "то", "что", "как", "это",
    "его", "ее", "её", "их", "ему", "ей", "нас", "вас", "них",
    "она", "они", "оно", "мы", "вы", "ты", "я", "меня", "тебя", "себя",
    "был", "была", "было", "были", "будет", "будут", "есть", "все",
    "весь", "эта", "этот", "эти", "та", "тот", "те", "такой", "такие",
    "который", "которая", "которое", "которые", "чтобы", "также",
    "можно", "нужно", "должен", "должна", "должны", "будто", "чтобы",
}


def score_movie(
    source: dict[str, Any],
    candidate: dict[str, Any],
    breakdown: dict[str, float] | None = None,
) -> float:
    score = 0.0
    components: dict[str, float] = {}

    source_genres = _genre_ids(source)
    candidate_genres = _genre_ids(candidate)
    genre_overlap = len(source_genres & candidate_genres)
    if source_genres:
        components["genre"] = (genre_overlap / len(source_genres)) * WEIGHT_GENRES
    else:
        components["genre"] = 0.0
    score += components["genre"]

    source_kw = set(source.get("keywords", []))
    candidate_kw = set(candidate.get("keywords", []))
    if source_kw:
        kw_overlap = len(source_kw & candidate_kw)
        components["keywords"] = (kw_overlap / len(source_kw)) * WEIGHT_KEYWORDS
    else:
        components["keywords"] = 0.0
    score += components["keywords"]

    components["overview"] = (
        _overlap_score(source.get("overview"), candidate.get("overview"))
        * WEIGHT_OVERVIEW
    )
    score += components["overview"]

    source_year = _year(source)
    candidate_year = _year(candidate)
    if source_year and candidate_year:
        diff = abs(source_year - candidate_year)
        year_factor = max(0.0, 1.0 - diff / MAX_YEAR_DIFF)
        components["year"] = year_factor * WEIGHT_YEAR
    else:
        components["year"] = 0.0
    score += components["year"]

    rating = candidate.get("vote_average") or 0
    components["rating"] = (rating / 10.0) * WEIGHT_RATING
    score += components["rating"]

    vote_count = candidate.get("vote_count") or 0
    pop_factor = math.log(vote_count + 1) / math.log(MAX_VOTE_COUNT + 1)
    components["popularity"] = pop_factor * WEIGHT_POPULARITY
    score += components["popularity"]

    source_director = (source.get("director") or "").strip().lower()
    candidate_director = (candidate.get("director") or "").strip().lower()
    if source_director and candidate_director == source_director:
        components["director"] = WEIGHT_DIRECTOR
    else:
        components["director"] = 0.0
    score += components["director"]

    source_cast = {name.strip().lower() for name in source.get("cast", []) if name and name.strip()}
    candidate_cast = {name.strip().lower() for name in candidate.get("cast", []) if name and name.strip()}
    if source_cast:
        cast_overlap = source_cast & candidate_cast
        components["cast"] = (len(cast_overlap) / len(source_cast)) * WEIGHT_CAST
    else:
        components["cast"] = 0.0
    score += components["cast"]

    source_tag = candidate.get("_source", "")
    if source_tag == "recommendation":
        components["endpoint_bonus"] = WEIGHT_BONUS
    elif source_tag == "similar":
        components["endpoint_bonus"] = WEIGHT_BONUS * 0.5
    else:
        components["endpoint_bonus"] = 0.0
    score += components["endpoint_bonus"]

    if genre_overlap < MIN_GENRE_OVERLAP:
        score *= 0.3

    if rating < RATING_THRESHOLD:
        score *= 0.5

    if vote_count < VOTE_COUNT_THRESHOLD:
        score *= 0.5

    if not candidate.get("overview"):
        score *= 0.85

    if breakdown is not None:
        breakdown.update(components)
        breakdown["total"] = score

    print("=" * 50)
    print(f"Movie: {candidate.get('title', '?')}")
    print(f"Genres ............. +{components['genre']:.2f}")
    print(f"Keywords ........... +{components['keywords']:.2f}")
    print(f"Overview ........... +{components['overview']:.2f}")
    print(f"Director ........... +{components['director']:.2f}")
    print(f"Cast ............... +{components['cast']:.2f}")
    print(f"Year ............... +{components['year']:.2f}")
    print(f"Rating ............. +{components['rating']:.2f}")
    print(f"Popularity ......... +{components['popularity']:.2f}")
    print(f"Endpoint bonus ..... +{components['endpoint_bonus']:.2f}")

    penalties: list[str] = []
    if genre_overlap < MIN_GENRE_OVERLAP:
        penalties.append(f"genre overlap < {MIN_GENRE_OVERLAP} (x0.30)")
    if rating < RATING_THRESHOLD:
        penalties.append(f"low rating: {rating:.1f} < {RATING_THRESHOLD} (x0.50)")
    if vote_count < VOTE_COUNT_THRESHOLD:
        penalties.append(f"low vote_count: {vote_count} < {VOTE_COUNT_THRESHOLD} (x0.50)")
    if not candidate.get("overview"):
        penalties.append("missing overview (x0.85)")

    if penalties:
        print("Penalty:")
        for p in penalties:
            print(f"- {p}")
    else:
        print("Penalty: none")
    print(f"TOTAL .............. {score:.2f}")
    print("=" * 50)

    return score


def _overlap_score(text_a: str | None, text_b: str | None) -> float:
    if not text_a or not text_b:
        return 0.0

    def tokenize(text: str) -> set[str]:
        words = re.findall(r"[а-яёa-z]+", text.lower())
        return {w for w in words if len(w) >= 4 and w not in STOP_WORDS}

    a_tokens = tokenize(text_a)
    b_tokens = tokenize(text_b)

    if not a_tokens or not b_tokens:
        return 0.0

    intersection = a_tokens & b_tokens
    union = a_tokens | b_tokens
    return len(intersection) / len(union)


def _genre_ids(movie: dict[str, Any]) -> set[int]:
    raw = movie.get("genre_ids") or movie.get("genres")
    if raw and isinstance(raw, list):
        return {g["id"] if isinstance(g, dict) else g for g in raw}
    return set()


def _year(movie: dict[str, Any]) -> int | None:
    date = movie.get("release_date")
    if date and len(date) >= 4:
        try:
            return int(date[:4])
        except ValueError:
            return None
    return None
