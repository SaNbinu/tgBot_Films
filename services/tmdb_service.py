import os
import requests
from typing import Any, Literal
from requests.exceptions import RequestException


from services.title_matcher import pick_best_match

TMDB_API_KEY: str | None = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
TMDB_LANGUAGE: str = "en-US"


class TMDBClient:
    """Client for The Movie Database (TMDB) API."""

    def __init__(self, api_key: str | None = None, language: str = TMDB_LANGUAGE) -> None:
        self.api_key: str | None = api_key or TMDB_API_KEY
        self.language: str = language
        self.base_url: str = TMDB_BASE_URL

    def _get(self, endpoint: str, params: dict | None = None) -> dict | None:
        if not self.api_key:
            raise ValueError("TMDB_API_KEY is not set. Provide a valid API key.")

        url = f"{self.base_url}{endpoint}"
        query_params: dict[str, Any] = {"api_key": self.api_key, "language": self.language}
        if params:
            query_params.update(params)

        try:
            response = requests.get(url, params=query_params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                return None
            raise
        except RequestException as e:
            raise ConnectionError(f"TMDB API request failed: {e}") from e

    def search_movie(self, title: str) -> dict | None:
        """Search for a movie by title and return the best matching result.

        The first TMDB result is not taken blindly: the closest title match
        is selected, comparing by lemma while ignoring case, punctuation and
        grammatical inflections. Results with extra words that are not part
        of the query (e.g. "Челюсти Крёстного отца" for "Крёстный отец")
        lose to an exact match. Returns None when no result matches closely
        enough, so the caller can try title normalization.

        Args:
            title: Movie title to search for.

        Returns:
            A dict with movie data if a close match was found, or None.
        """
        data = self._get("/search/movie", {"query": title})
        if not data:
            return None
        results = data.get("results")
        if not results:
            return None
        best = pick_best_match(title, results)
        print(f"search_movie: {len(results)} result(s), best match: {best.get('title') if best else None}")
        if best is None:
            return None
        return {
            "id": best["id"],
            "title": best["title"],
            "original_title": best["original_title"],
            "overview": best.get("overview"),
            "release_date": best.get("release_date"),
            "vote_average": best.get("vote_average"),
            "vote_count": best.get("vote_count"),
            "poster_path": best.get("poster_path"),
            "genre_ids": best.get("genre_ids", []),
        }

    def get_similar_movies(self, movie_id: int, limit: int = 10) -> list[dict]:
        """Find movies similar to the given movie.

        Args:
            movie_id: TMDB movie ID.
            limit: Maximum number of results to return (default 10).

        Returns:
            A list of similar movies, each with id, title, overview,
            release_date, vote_average, poster_path.
        """
        data = self._get(f"/movie/{movie_id}/similar")
        if not data:
            return []
        results = data.get("results", [])
        return [
            {
                "id": m["id"],
                "title": m["title"],
                "overview": m.get("overview"),
                "release_date": m.get("release_date"),
                "vote_average": m.get("vote_average"),
                "vote_count": m.get("vote_count"),
                "popularity": m.get("popularity"),
                "poster_path": m.get("poster_path"),
            }
            for m in results[:limit]
        ]

    def get_recommendations(self, movie_id: int, limit: int = 20) -> list[dict]:
        """Get movie recommendations from /movie/{id}/recommendations.

        Args:
            movie_id: TMDB movie ID.
            limit: Maximum number of results to return (default 20).

        Returns:
            A list of recommended movies with id, title, overview,
            release_date, vote_average, vote_count, popularity,
            poster_path, genre_ids.
        """
        data = self._get(f"/movie/{movie_id}/recommendations")
        if not data:
            return []
        results = data.get("results", [])
        return [
            {
                "id": m["id"],
                "title": m["title"],
                "overview": m.get("overview"),
                "release_date": m.get("release_date"),
                "vote_average": m.get("vote_average"),
                "vote_count": m.get("vote_count"),
                "popularity": m.get("popularity"),
                "poster_path": m.get("poster_path"),
                "genre_ids": m.get("genre_ids", []),
            }
            for m in results[:limit]
        ]

    def get_movie_keywords(self, movie_id: int) -> list[str]:
        """Get keywords for a movie from /movie/{id}/keywords.

        Args:
            movie_id: TMDB movie ID.

        Returns:
            A list of keyword strings, or an empty list if none found.
        """
        data = self._get(f"/movie/{movie_id}/keywords")
        if not data:
            return []
        return [kw["name"] for kw in data.get("keywords", [])]

    def get_movie_people(self, movie_id: int) -> dict:
        """Get the director and main cast for a movie from /movie/{id}/credits.

        Args:
            movie_id: TMDB movie ID.

        Returns:
            A dict with "director" (str) and "cast" (list of str) keys.
            Empty values if no credits data is available.
        """
        data = self._get(f"/movie/{movie_id}/credits")
        if not data:
            return {"director": "", "cast": []}

        director = ""
        for crew in data.get("crew", []):
            if crew.get("job") == "Director":
                director = crew.get("name", "")
                break

        cast = [m.get("name", "") for m in data.get("cast", [])[:7] if m.get("name")]

        return {"director": director, "cast": cast}

    def get_movie_details(self, movie_id: int) -> dict | None:
        """Get full details for a movie by its TMDB ID.

        Args:
            movie_id: TMDB movie ID.

        Returns:
            A dict with full movie details, or None if not found.
            Includes id, title, original_title, overview, release_date,
            vote_average, vote_count, poster_path, backdrop_path, genres,
            runtime, budget, revenue, tagline, status, homepage, imdb_id,
            production_companies, production_countries and original_language.
        """
        data = self._get(f"/movie/{movie_id}")
        if not data:
            return None
        return {
            "id": data["id"],
            "title": data["title"],
            "original_title": data["original_title"],
            "overview": data.get("overview"),
            "release_date": data.get("release_date"),
            "vote_average": data.get("vote_average"),
            "vote_count": data.get("vote_count"),
            "poster_path": data.get("poster_path"),
            "backdrop_path": data.get("backdrop_path"),
            "genres": data.get("genres", []),
            "runtime": data.get("runtime"),
            "budget": data.get("budget"),
            "revenue": data.get("revenue"),
            "tagline": data.get("tagline"),
            "status": data.get("status"),
            "homepage": data.get("homepage"),
            "imdb_id": data.get("imdb_id"),
            "production_companies": data.get("production_companies", []),
            "production_countries": data.get("production_countries", []),
            "original_language": data.get("original_language"),
        }

    def get_poster_url(self, poster_path: str | None, size: str = "w500") -> str | None:
        """Build a full TMDB poster URL from a poster path.

        Args:
            poster_path: A poster path from TMDB (e.g. "/abc.jpg").
            size: Image size variant (default "w500").

        Returns:
            A full https URL to the poster image, or None if no path given.
        """
        if not poster_path:
            return None
        return f"https://image.tmdb.org/t/p/{size}{poster_path}"

    def search_person(self, name: str, language: str | None = None) -> dict | None:
        """Search for a person (actor, director, etc.) by name.

        Args:
            name: Person name to search for.
            language: Language override (e.g. "en-US"). Uses instance default if None.

        Returns:
            A dict with person data if found, or None if no results.
        """
        params: dict[str, Any] = {"query": name}
        if language is not None:
            params["language"] = language
        data = self._get("/search/person", params)
        if not data:
            return None
        results = data.get("results")
        if not results:
            return None
        first = results[0]
        return {
            "id": first["id"],
            "name": first["name"],
            "known_for_department": first.get("known_for_department"),
            "popularity": first.get("popularity"),
            "profile_path": first.get("profile_path"),
            "known_for": first.get("known_for", []),
        }

    def get_person_movies(self, person_id: int, role: Literal["actor", "director"] = "actor") -> list[dict]:
        """Get movies a person has participated in.

        Args:
            person_id: TMDB person ID.
            role: "actor" for cast roles, "director" for directed films.

        Returns:
            A list of movies with id, title, character/job, release_date,
            vote_average, poster_path.
        """
        data = self._get(f"/person/{person_id}/movie_credits")
        if not data:
            return []

        if role == "actor":
            cast = data.get("cast", [])
            return [
                {
                    "id": m["id"],
                    "title": m["title"],
                    "character": m.get("character"),
                    "release_date": m.get("release_date"),
                    "vote_average": m.get("vote_average"),
                    "vote_count": m.get("vote_count"),
                    "overview": m.get("overview"),
                    "poster_path": m.get("poster_path"),
                }
                for m in cast
            ]

        crew = data.get("crew", [])
        directed = [m for m in crew if m.get("job") == "Director"]
        return [
            {
                "id": m["id"],
                "title": m["title"],
                "job": m.get("job"),
                "release_date": m.get("release_date"),
                "vote_average": m.get("vote_average"),
                "vote_count": m.get("vote_count"),
                "overview": m.get("overview"),
                "poster_path": m.get("poster_path"),
            }
            for m in directed
        ]

    def get_genres(self) -> list[dict]:
        """Get a list of all TMDB movie genres.

        Returns:
            A list of genres, each with id and name.
        """
        data = self._get("/genre/movie/list")
        if not data:
            return []
        return data.get("genres", [])

    def discover_movies(
        self,
        with_genres: str | None = None,
        primary_release_year: int | None = None,
        vote_average_gte: float | None = None,
        sort_by: str | None = None,
        with_original_language: str | None = None,
        page: int = 1,
    ) -> list[dict]:
        """Discover movies using TMDB /discover/movie endpoint.

        Args:
            with_genres: Comma-separated genre IDs to filter by.
            primary_release_year: Filter by primary release year.
            vote_average_gte: Minimum vote average.
            sort_by: Sort option (e.g. "popularity.desc", "vote_average.desc").
            with_original_language: Filter by original language code (e.g. "en", "fr").
            page: Page number (default 1).

        Returns:
            A list of discovered movies with id, title, overview,
            release_date, vote_average, vote_count, poster_path, genre_ids.
        """
        params: dict[str, Any] = {"page": page}
        if with_genres:
            params["with_genres"] = with_genres
        if primary_release_year:
            params["primary_release_year"] = primary_release_year
        if vote_average_gte is not None:
            params["vote_average.gte"] = vote_average_gte
        if sort_by:
            params["sort_by"] = sort_by
        if with_original_language:
            params["with_original_language"] = with_original_language

        data = self._get("/discover/movie", params)
        if not data:
            return []
        results = data.get("results", [])
        return [
            {
                "id": m["id"],
                "title": m["title"],
                "overview": m.get("overview"),
                "release_date": m.get("release_date"),
                "vote_average": m.get("vote_average"),
                "vote_count": m.get("vote_count"),
                "poster_path": m.get("poster_path"),
                "genre_ids": m.get("genre_ids", []),
            }
            for m in results
        ]

