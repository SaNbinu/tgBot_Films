from dataclasses import dataclass


@dataclass
class RecommendationResult:
    """Represents the result of a movie recommendation request.

    Attributes:
        success: Whether the recommendation was successfully generated.
        message: A human-readable response text for the user.
        movies: A list of movie dicts that were used or found.
    """

    success: bool
    message: str
    movies: list[dict]
