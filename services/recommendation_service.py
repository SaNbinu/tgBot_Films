import re
import time
from datetime import datetime
from typing import Literal
from services.query_analyzer import QueryAnalyzer, QueryType, AnalysisResult
from services.tmdb_service import TMDBClient
from services.ollama_service import OllamaService
from services.movie_scorer import score_movie
from services.recommendation_result import RecommendationResult

GENRE_RU_TO_TMDB: dict[str, int] = {
    "боевик": 28, "боевики": 28, "боевика": 28, "боевиков": 28,
    "комедия": 35, "комедии": 35, "комедию": 35, "комедийный": 35,
    "ужасы": 27, "ужасов": 27, "ужастик": 27, "ужастики": 27, "ужастиков": 27,
    "фантастика": 878, "фантастику": 878, "фантастический": 878,
    "фантастические": 878, "фантастических": 878,
    "драма": 18, "драмы": 18, "драму": 18,
    "триллер": 53, "триллеры": 53, "триллера": 53, "триллеров": 53,
    "мелодрама": 10749, "мелодрамы": 10749, "мелодраму": 10749,
    "детектив": 9648, "детективы": 9648, "детектива": 9648,
    "детективов": 9648, "детективный": 9648,
    "приключения": 12, "приключенческий": 12, "приключенческие": 12,
    "приключенческих": 12,
    "мультфильм": 16, "мультфильмы": 16, "мультфильмов": 16,
    "мультик": 16, "мультики": 16, "мультиков": 16, "мульт": 16,
    "аниме": 16,
    "фэнтези": 14,
    "вестерн": 37, "вестерны": 37,
    "документальный": 99,
    "исторический": 36,
    "военный": 10752, "военные": 10752, "военных": 10752,
    "музыкальный": 10402,
    "криминал": 80, "криминальный": 80, "криминала": 80,
    "семейный": 10751, "семейные": 10751, "семейных": 10751,
}

GENRE_THEME_TO_TMDB: dict[str, int] = {
    "космос": 878,
    "войну": 10752,
    "зомби": 27,
    "вампиров": 27,
}


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
        t_start = time.perf_counter()

        t0 = time.perf_counter()
        result: AnalysisResult = self.analyzer.analyze(user_query)
        print(f"QueryAnalyzer: {time.perf_counter() - t0:.3f} sec")
        print(f"  query_type={result.query_type}, value={result.value!r}")

        if result.query_type == QueryType.SIMILAR_MOVIE:
            res = self._handle_similar_movie(user_query, result.value)
            print(f"Total recommend(): {time.perf_counter() - t_start:.3f} sec")
            return res

        if result.query_type == QueryType.PERSON:
            return self._handle_person(result.value)

        if result.query_type == QueryType.GENRE:
            return self._handle_genre(result.value)

        return self._handle_ai_required(user_query)

    def _handle_similar_movie(self, user_query: str, movie_title: str | None) -> RecommendationResult:
        """Find top 3 similar movies using TMDB data + custom MovieScorer."""
        print(f"=== SIMILAR_MOVIE DEBUG ===")
        print(f"user_query = {user_query!r}")
        print(f"movie_title = {movie_title!r}")

        if not movie_title:
            return RecommendationResult(
                success=False,
                message="Укажите название фильма.",
                movies=[],
            )

        t0 = time.perf_counter()
        print(f"Calling search_movie with: {movie_title!r}")
        movie = self.tmdb.search_movie(movie_title)
        print(f"search_movie: {time.perf_counter() - t0:.3f} sec")
        print(f"search_movie result: {movie.get('title', 'N/A') if movie else None}")
        if not movie:
            print("  -> search_movie returned None. Trying Ollama normalization.")
            try:
                normalized = self.ollama.normalize_movie_title(movie_title)
            except Exception as e:
                print(f"  -> Ollama normalization failed: {e}")
                normalized = ""
            if normalized:
                print(f"  -> Normalized title: {normalized!r}")
                t0 = time.perf_counter()
                movie = self.tmdb.search_movie(normalized)
                print(f"  -> Retry search_movie: {time.perf_counter() - t0:.3f} sec")
                print(f"  -> Retry result: {movie.get('title', 'N/A') if movie else None}")
        if not movie:
            print("  -> Movie not found by TMDB after normalization.")
            return RecommendationResult(
                success=False,
                message="Фильм не найден.",
                movies=[],
            )

        source_id = movie["id"]
        seen_ids: set[int] = set()
        raw_candidates: list[dict] = []

        t0 = time.perf_counter()
        for r in self.tmdb.get_recommendations(source_id, limit=10):
            if r["id"] != source_id and r["id"] not in seen_ids:
                r["_source"] = "recommendation"
                raw_candidates.append(r)
                seen_ids.add(r["id"])
        print(f"get_recommendations: {time.perf_counter() - t0:.3f} sec")

        t0 = time.perf_counter()
        for s in self.tmdb.get_similar_movies(source_id, limit=10):
            if s["id"] != source_id and s["id"] not in seen_ids:
                s["_source"] = "similar"
                raw_candidates.append(s)
                seen_ids.add(s["id"])
        print(f"get_similar_movies: {time.perf_counter() - t0:.3f} sec")

        t0 = time.perf_counter()
        details = self.tmdb.get_movie_details(source_id)
        print(f"get_movie_details: {time.perf_counter() - t0:.3f} sec")
        if not details:
            return RecommendationResult(
                success=False,
                message="Не удалось получить информацию о фильме.",
                movies=[],
            )

        if len(raw_candidates) < 10:
            genre_ids = [str(g["id"]) for g in details.get("genres", [])]
            genre_str = ",".join(genre_ids) if genre_ids else ""
            if genre_str:
                t0 = time.perf_counter()
                for d in self.tmdb.discover_movies(
                    with_genres=genre_str,
                    vote_average_gte=6.5,
                    sort_by="vote_count.desc",
                    page=1,
                ):
                    if d["id"] != source_id and d["id"] not in seen_ids:
                        d["_source"] = "discover"
                        raw_candidates.append(d)
                        seen_ids.add(d["id"])
                print(f"discover_movies: {time.perf_counter() - t0:.3f} sec")
        else:
            print("discover_movies: SKIPPED (recommendations + similar >= 10)")

        recs = [c for c in raw_candidates if c.get("_source") == "recommendation"]
        sims = [c for c in raw_candidates if c.get("_source") == "similar"]
        disc = [c for c in raw_candidates if c.get("_source") == "discover"]
        print(f"Candidates by source: recommendations={len(recs)}, similar={len(sims)}, discover={len(disc)}")

        print(f"Total raw candidates: {len(raw_candidates)}")
        if not raw_candidates:
            return RecommendationResult(
                success=False,
                message="Похожие фильмы не найдены.",
                movies=[],
            )

        details["keywords"] = self.tmdb.get_movie_keywords(source_id)
        print(f"Source keywords ({movie.get('title', '?')}): {details.get('keywords', [])}")
        print(f"Source keywords are EMPTY: {not details.get('keywords')}")

        details["director"] = ""
        details["cast"] = []
        try:
            people = self.tmdb.get_movie_people(source_id)
            details["director"] = people.get("director", "")
            details["cast"] = people.get("cast", [])
        except Exception as e:
            print(f"get_movie_people (source): FAILED {e}")

        for c in raw_candidates:
            c["keywords"] = self.tmdb.get_movie_keywords(c["id"])
            c["director"] = ""
            c["cast"] = []
            try:
                people = self.tmdb.get_movie_people(c["id"])
                c["director"] = people.get("director", "")
                c["cast"] = people.get("cast", [])
            except Exception as e:
                print(f"get_movie_people ({c.get('title', '?')}): FAILED {e}")

        def _score_and_sort(group: list[dict], label: str) -> list[tuple[float, dict[str, float], dict]]:
            if not group:
                return []
            result: list[tuple[float, dict[str, float], dict]] = []
            print(f"\n--- {label} ---")
            for c in group:
                components: dict[str, float] = {}
                total = score_movie(details, c, breakdown=components)

                c_kw = set(c.get("keywords", []))
                s_kw = set(details.get("keywords", []))
                overlap = s_kw & c_kw
                kw_score = components.get("keywords", 0.0) if s_kw else 0.0
                endpoint_bonus = components.get("endpoint_bonus", 0.0)

                print(f"\n  {c.get('title', '?')}")
                print(f"    _source = {c.get('_source', 'N/A')}")
                print(f"    endpoint_bonus = {endpoint_bonus:.2f}")
                print(f"    director match: {components.get('director', 0.0) > 0}")
                shared = sorted(
                    {n.strip().lower() for n in details.get("cast", []) if n and n.strip()}
                    & {n.strip().lower() for n in c.get("cast", []) if n and n.strip()}
                )
                print(f"    shared actors: {shared}")
                print(f"    cast score: {components.get('cast', 0.0):.2f}")
                print(f"    source keywords ({len(s_kw)}): {sorted(s_kw)}")
                print(f"    source keywords EMPTY: {not s_kw}")
                print(f"    candidate keywords ({len(c_kw)}): {sorted(c_kw)}")
                print(f"    candidate keywords EMPTY: {not c_kw}")
                print(f"    keyword overlap: {sorted(overlap)}")
                print(f"    keyword score: {kw_score:.2f}")
                print(f"    overview score: {components.get('overview', 0.0):.2f}")

                result.append((total, components, c))
            result.sort(key=lambda x: x[0], reverse=True)
            return result

        scored_recs = _score_and_sort(recs, "RECOMMENDATIONS")
        scored_sims = _score_and_sort(sims, "SIMILAR")
        scored_disc = _score_and_sort(disc, "DISCOVER")

        all_scored = sorted(
            scored_recs + scored_sims + scored_disc,
            key=lambda x: x[0],
            reverse=True,
        )
        top10_candidates = [c for _, _, c in all_scored[:10]]
        print("=== TOP-10 CANDIDATES ===")
        for i, c in enumerate(top10_candidates, 1):
            print(f"  {i}. {c.get('title', '?')} (score={all_scored[i-1][0]:.2f}, _source={c.get('_source', '?')})")

        ollama_titles: list[str] = []
        try:
            ollama_titles = self.ollama.rerank_movies(user_query, top10_candidates, source_movie=movie)
        except Exception as e:
            print(f"Ollama rerank failed: {e}")

        title_to_movie: dict[str, dict] = {}
        for c in raw_candidates:
            title = (c.get("title") or "").strip()
            if title:
                title_to_movie[title.lower()] = c

        selected: list[dict] = []
        seen_ids: set[int] = set()
        ollama_used = False

        print("=== OLLAMA TITLE MATCHING ===")
        for t in ollama_titles:
            t_clean = t.strip().lower()
            match = title_to_movie.get(t_clean)
            if match:
                print(f"  MATCHED: '{t}' -> {match.get('title', '?')} (id={match['id']})")
            else:
                print(f"  NOT FOUND: '{t}' — no match in candidates")
            if match and match["id"] not in seen_ids:
                selected.append(match)
                seen_ids.add(match["id"])
                ollama_used = True

        if not ollama_used:
            print("  -> Ollama returned 0 valid titles. Full fallback to MovieScorer.")
        elif len(selected) < 3:
            print(f"  -> Ollama returned only {len(selected)} valid title(s). Filling rest from MovieScorer.")
        else:
            print(f"  -> Ollama returned {len(selected)} valid titles. Using Ollama selection.")

        if not ollama_used or len(selected) < 3:
            print("Ollama selection incomplete — falling back to MovieScorer ranking")
            selected = []
            seen_ids.clear()

            for _, _, c in scored_recs[:2]:
                if c["id"] not in seen_ids:
                    selected.append(c)
                    seen_ids.add(c["id"])

            for _, _, c in scored_sims[:1]:
                if c["id"] not in seen_ids:
                    selected.append(c)
                    seen_ids.add(c["id"])

            if len(selected) < 3:
                for _, _, c in scored_disc:
                    if c["id"] not in seen_ids:
                        selected.append(c)
                        seen_ids.add(c["id"])
                        if len(selected) >= 3:
                            break

        top3 = selected[:3]

        text = "🎬 Похожие фильмы:\n\n"
        for i, m in enumerate(top3, 1):
            title = m.get("title", "Unknown")
            year = m.get("release_date", "")[:4] if m.get("release_date") else "N/A"
            rating = m.get("vote_average", "N/A")
            overview = m.get("overview")
            if overview:
                if len(overview) > 220:
                    overview = overview[:220].rsplit(" ", 1)[0] + "..."
            else:
                overview = "Описание отсутствует."
            text += f"{i}. {title} ({year})\n⭐ Рейтинг TMDB: {rating}\n\n{overview}\n\n"
            if i < len(top3):
                text += "----------------\n\n"

        return RecommendationResult(
            success=True,
            message=text.strip(),
            movies=top3,
        )

    def _handle_person(self, value: str | None) -> RecommendationResult:
        """Handle a request for movies by a specific person (actor/director).

        Searches for the person via TMDB, determines their role, fetches
        their filmography, deduplicates, sorts by rating+votes, and returns
        the top 5 movies.
        """
        if not value:
            return RecommendationResult(
                success=False,
                message="Укажите имя актёра или режиссёра.",
                movies=[],
            )

        t0 = time.perf_counter()
        person = self.tmdb.search_person(value)
        print(f"search_person (ru): {time.perf_counter() - t0:.3f} sec")
        if not person:
            normalized = _normalize_name(value)
            if normalized:
                t0 = time.perf_counter()
                person = self.tmdb.search_person(normalized)
                print(f"search_person normalized (ru): {time.perf_counter() - t0:.3f} sec ({normalized})")
            if not person:
                t0 = time.perf_counter()
                person = self.tmdb.search_person(value, language="en-US")
                print(f"search_person (en): {time.perf_counter() - t0:.3f} sec")
            if not person:
                return RecommendationResult(
                    success=False,
                    message="Актёр или режиссёр не найден.",
                    movies=[],
                )

        department = person.get("known_for_department", "")
        role: Literal["actor", "director"] = "director" if department == "Directing" else "actor"
        display_name = person["name"]
        print(f"Person: {display_name}, role: {role}")

        t0 = time.perf_counter()
        movies = self.tmdb.get_person_movies(person["id"], role)
        print(f"get_person_movies: {time.perf_counter() - t0:.3f} sec ({len(movies)} movies)")

        EXCLUDED_KEYWORDS = [
            "making", "behind", "featurette", "special", "interview",
            "documentary", "documental", "bonus", "extras", "scorsese",
            "learning", "club", "meditation", "night of", "doctor who",
            "bastidores",
        ]
        exclude_pattern = re.compile(
            "|".join(re.escape(kw) for kw in EXCLUDED_KEYWORDS),
            re.IGNORECASE,
        )

        filtered: list[dict] = []
        for m in movies:
            if (m.get("vote_count") or 0) < 1000:
                continue
            if not m.get("overview"):
                continue
            if not m.get("release_date"):
                continue
            media_type = m.get("media_type")
            if media_type is not None and media_type != "movie":
                continue
            title = m.get("title") or ""
            if exclude_pattern.search(title):
                continue
            filtered.append(m)

        if not filtered:
            return RecommendationResult(
                success=False,
                message=f"У {display_name} не найдено фильмов в роли {'режиссёра' if role == 'director' else 'актёра'}.",
                movies=[],
            )

        seen_ids: set[int] = set()
        unique: list[dict] = []
        for m in filtered:
            if m["id"] not in seen_ids:
                seen_ids.add(m["id"])
                unique.append(m)

        unique.sort(key=lambda m: (-(m.get("vote_average") or 0), -(m.get("vote_count") or 0)))
        top = unique[:5]

        header = "🎬 Фильмы режиссёра" if role == "director" else "🎬 Фильмы с"
        text = f"{header} {display_name}:\n\n"
        for i, m in enumerate(top, 1):
            title = m.get("title", "Unknown")
            year = m.get("release_date", "")[:4] if m.get("release_date") else "N/A"
            rating = m.get("vote_average", "N/A")
            overview = m.get("overview")
            if overview:
                if len(overview) > 220:
                    overview = overview[:220].rsplit(" ", 1)[0] + "..."
            else:
                overview = "Описание отсутствует."
            text += f"{i}. {title} ({year})\n⭐ Рейтинг TMDB: {rating}\n\n{overview}\n\n"
            if i < len(top):
                text += "----------------\n\n"

        return RecommendationResult(
            success=True,
            message=text.strip(),
            movies=top,
        )

    def _handle_genre(self, value: str | None) -> RecommendationResult:
        """Handle a request for movies of a specific genre.

        Maps the Russian keyword or theme to a TMDB genre ID, fetches
        multiple pages of discover results, deduplicates, filters by
        vote_average >= 7 and vote_count >= 1000, sorts, and returns top 5.
        """
        if not value:
            return RecommendationResult(
                success=False,
                message="Укажите жанр.",
                movies=[],
            )

        genre_id = GENRE_THEME_TO_TMDB.get(value) or GENRE_RU_TO_TMDB.get(value)
        if not genre_id:
            return RecommendationResult(
                success=False,
                message=f"Жанр «{value}» не найден.",
                movies=[],
            )

        genres = self.tmdb.get_genres()
        genre_display = next(
            (g["name"] for g in genres if g["id"] == genre_id), str(genre_id)
        )

        t0 = time.perf_counter()
        seen_ids: set[int] = set()
        candidates: list[dict] = []
        for page in range(1, 6):
            batch = self.tmdb.discover_movies(
                with_genres=str(genre_id),
                sort_by="popularity.desc",
                page=page,
            )
            if not batch:
                break
            for m in batch:
                if m["id"] not in seen_ids:
                    seen_ids.add(m["id"])
                    candidates.append(m)
        print(f"discover_movies (genre): {time.perf_counter() - t0:.3f} sec ({len(candidates)} candidates)")

        if not candidates:
            return RecommendationResult(
                success=False,
                message=f"Фильмы жанра «{genre_display}» не найдены.",
                movies=[],
            )

        with_overview = [m for m in candidates if m.get("overview")]
        without_overview = [m for m in candidates if not m.get("overview")]

        def _is_old_enough(m: dict) -> bool:
            date = m.get("release_date")
            if not date or len(date) < 10:
                return False
            try:
                release = datetime.strptime(date[:10], "%Y-%m-%d")
                return (datetime.now() - release).days >= 365
            except ValueError:
                return False

        def _dedup_franchises(movies: list[dict]) -> list[dict]:
            seen: set[str] = set()
            result: list[dict] = []
            for m in movies:
                base = normalize_franchise_title(m.get("title", ""))
                if base not in seen:
                    seen.add(base)
                    result.append(m)
            return result

        vote_thresholds = [3000, 2000, 1000]
        top = []
        for threshold in vote_thresholds:
            pool = [
                m for m in with_overview
                if (m.get("vote_count") or 0) >= threshold
                and _is_old_enough(m)
            ]
            pool.sort(key=lambda m: (-(m.get("vote_average") or 0), -(m.get("vote_count") or 0)))
            pool = _dedup_franchises(pool)
            top = pool[:5]
            if len(top) >= 5:
                break

        if len(top) < 5:
            needed = 5 - len(top)
            fallback = [
                m for m in without_overview
                if (m.get("vote_count") or 0) >= 1000
                and _is_old_enough(m)
            ]
            fallback.sort(key=lambda m: (-(m.get("vote_average") or 0), -(m.get("vote_count") or 0)))
            fallback = _dedup_franchises(fallback)
            top.extend(fallback[:needed])

        print("Genre candidates:", len(candidates))
        print("After filters:", len(top))
        print("Top 10:")
        all_sorted = sorted(
            with_overview + without_overview,
            key=lambda m: (-(m.get("vote_average") or 0), -(m.get("vote_count") or 0)),
        )
        for movie in all_sorted[:10]:
            print(movie["title"], movie["vote_average"], movie["vote_count"])

        text = f"🎬 Лучшие фильмы жанра «{genre_display}»:\n\n"
        for i, m in enumerate(top, 1):
            title = m.get("title", "Unknown")
            year = m.get("release_date", "")[:4] if m.get("release_date") else "N/A"
            rating = m.get("vote_average", "N/A")
            overview = m.get("overview")
            if overview:
                if len(overview) > 220:
                    overview = overview[:220].rsplit(" ", 1)[0] + "..."
            else:
                overview = "Описание отсутствует."
            text += f"{i}. {title} ({year})\n⭐ Рейтинг TMDB: {rating}\n\n{overview}\n\n"
            if i < len(top):
                text += "----------------\n\n"

        return RecommendationResult(
            success=True,
            message=text.strip(),
            movies=top,
        )

    def _handle_ai_required(self, user_query: str) -> RecommendationResult:
        """Handle a complex request that requires AI processing."""
        try:
            text = self.ollama.generate_response(user_query)
        except Exception as e:
            return RecommendationResult(
                success=False,
                message=f"Не удалось обработать запрос: {e}",
                movies=[],
            )
        return RecommendationResult(
            success=True,
            message=text.strip(),
            movies=[],
        )


def _normalize_name(name: str) -> str | None:
    """Strip Russian case endings from a name to recover the nominative form.

    Tries removing common declension suffixes (instrumental -om, -em, genitive
    -a, -ya, etc.) word by word. Returns the normalized name if any word
    changed, otherwise None.
    """
    ENDINGS = [
        "ого", "его", "ому", "ему",
        "ым", "им", "ой", "ом", "ем",
        "ую", "юю", "а", "я", "ы", "и",
        "у", "ю", "е",
    ]
    words = name.split()
    changed = False
    normalized: list[str] = []
    for word in words:
        lower = word.lower()
        for ending in ENDINGS:
            if lower.endswith(ending) and len(word) > len(ending) + 1:
                word = word[:-len(ending)]
                changed = True
                break
        normalized.append(word)
    return " ".join(normalized) if changed else None


def normalize_franchise_title(title: str) -> str:
    """Extract the base franchise name from a movie title.

    Strips everything after the first colon, trailing episode indicators
    (Часть/Part/Chapter/Episode + number), and trailing Arabic/Roman numerals.
    """
    base = title.split(":")[0].strip()
    if not base:
        return title.strip()

    base = re.sub(
        r"\s*[-–—]\s*(?:Часть|Part|Chapter|Episode|Глава|Эпизод|Vol\.?)\s+\w+\s*$",
        "", base, flags=re.IGNORECASE,
    ).strip()
    base = re.sub(
        r"\s*[(](?:Часть|Part|Chapter|Episode|Глава|Эпизод|Vol\.?)\s+\w+[)]\s*$",
        "", base, flags=re.IGNORECASE,
    ).strip()

    base = re.sub(r"\s+\d+\s*$", "", base).strip()

    for roman in ["VIII", "III", "VII", "IV", "IX", "VI", "II", "V", "I", "X"]:
        if base.endswith(f" {roman}"):
            base = base[:-(len(roman) + 1)].strip()
            break

    base = re.sub(r"\s+", " ", base).strip()
    return base if base else title.strip()

