import os
import requests
from typing import Any, Literal
from requests.exceptions import RequestException


TMDB_API_KEY: str | None = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
TMDB_LANGUAGE: str = "ru-RU"


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
        """Search for a movie by title and return the first result.

        Args:
            title: Movie title to search for.

        Returns:
            A dict with movie data if found, or None if no results.
        """
        data = self._get("/search/movie", {"query": title})
        if not data:
            return None
        results = data.get("results")
        if not results:
            return None
        first = results[0]
        return {
            "id": first["id"],
            "title": first["title"],
            "original_title": first["original_title"],
            "overview": first.get("overview"),
            "release_date": first.get("release_date"),
            "vote_average": first.get("vote_average"),
            "vote_count": first.get("vote_count"),
            "poster_path": first.get("poster_path"),
            "genre_ids": first.get("genre_ids", []),
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
                "poster_path": m.get("poster_path"),
            }
            for m in results[:limit]
        ]

    def get_movie_details(self, movie_id: int) -> dict | None:
        """Get full details for a movie by its TMDB ID.

        Args:
            movie_id: TMDB movie ID.

        Returns:
            A dict with full movie details, or None if not found.
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
        }

    def search_person(self, name: str) -> dict | None:
        """Search for a person (actor, director, etc.) by name.

        Args:
            name: Person name to search for.

        Returns:
            A dict with person data if found, or None if no results.
        """
        data = self._get("/search/person", {"query": name})
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
            release_date, vote_average, poster_path, genre_ids.
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
                "poster_path": m.get("poster_path"),
                "genre_ids": m.get("genre_ids", []),
            }
            for m in results
        ]

