import re
from typing import Any

try:
    import pymorphy3

    _MORPH: Any = pymorphy3.MorphAnalyzer()
except ImportError:
    _MORPH = None

_WORD_RE = re.compile(r"[0-9a-zа-яё]+")


def _normalize(text: str) -> str:
    return text.lower().replace("ё", "е")


def _lemma(word: str) -> str:
    word = _normalize(word)
    if _MORPH is not None:
        return _MORPH.parse(word)[0].normal_form.replace("ё", "е")
    return word


def _token_keys(text: str) -> set[str]:
    return {_lemma(w) for w in _WORD_RE.findall(text.lower())}


def pick_best_match(query: str, results: list[dict]) -> dict | None:
    """Return the movie whose title best matches the query.

    A result is considered a match only if its title (or original title)
    contains exactly the same words as the query, compared by lemma with
    case, punctuation and grammatical inflections normalized. Any result
    with extra words (e.g. "Челюсти Крёстного отца" for "Крёстный отец")
    is rejected. Returns None when no result matches closely enough.
    """
    query_keys = _token_keys(query)
    if not query_keys:
        return None
    for result in results:
        title = result.get("title") or ""
        original_title = result.get("original_title") or ""
        for field in (title, original_title):
            if field and _token_keys(field) == query_keys:
                return result
    return None
