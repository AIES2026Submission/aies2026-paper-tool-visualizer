import re
from typing import Tuple


VALID_RATINGS = (
    "strongly agree",
    "agree",
    "neutral",
    "disagree",
    "strongly disagree",
)

_RATING_VALUE_PATTERN = r"(?:strongly\s+)?(?:agrees?|disagrees?|neutral)"
_PRIMARY_PATTERN = re.compile(
    rf"(?:Analysis\*?\*?:?)\s+(.*)\s+(?:Rating\*?\*?:?)\s+({_RATING_VALUE_PATTERN})",
    re.DOTALL | re.IGNORECASE,
)
_ANALYSIS_MARKER = re.compile(
    r"(?:\*\*|\*|_)?(?:\d+\.|\*|-)?\s*Analysis(?:\*\*|\*|_)?[: ]",
    re.IGNORECASE,
)
_RATING_MARKER = re.compile(
    r"(?:\*\*|\*|_)?(?:\d+\.|\*|-)?\s*Rating(?:\*\*|\*|_)?[: ]",
    re.IGNORECASE,
)
_RATING_KEYWORD = re.compile(
    r"\b(?:" + "|".join(re.escape(rating) for rating in VALID_RATINGS) + r")\b",
    re.IGNORECASE,
)


def _normalize_rating(value: str) -> str:
    return value.strip().lower().replace("agrees", "agree").replace("disagrees", "disagree")


def get_judge_analysis_and_rating(judge_reply_text: str) -> Tuple[str, str]:
    invalid_analysis = "Error: Could not parse analysis."
    invalid_rating = "Error: Could not parse rating."

    if not isinstance(judge_reply_text, str) or not judge_reply_text:
        error = "Error: Invalid judge reply text"
        return error, error

    primary_match = _PRIMARY_PATTERN.search(judge_reply_text)
    if primary_match:
        analysis = primary_match.group(1).strip()
        rating = _normalize_rating(primary_match.group(2))
        if rating in VALID_RATINGS:
            return analysis, rating

    analysis_marker = _ANALYSIS_MARKER.search(judge_reply_text)
    rating_marker = _RATING_MARKER.search(judge_reply_text)
    if not analysis_marker or not rating_marker:
        return invalid_analysis, invalid_rating
    if analysis_marker.end() >= rating_marker.start():
        return invalid_analysis, invalid_rating

    analysis = judge_reply_text[analysis_marker.end():rating_marker.start()].strip()
    rating_match = _RATING_KEYWORD.search(judge_reply_text[rating_marker.end():])
    if not rating_match:
        return analysis, invalid_rating

    rating = _normalize_rating(rating_match.group(0))
    if rating not in VALID_RATINGS:
        return analysis, invalid_rating
    return analysis, rating
