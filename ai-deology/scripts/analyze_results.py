import json
import pathlib
import argparse
import statistics
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple

RATING_TO_SCORE = {
    "strongly disagree": -2,
    "disagree": -1,
    "neutral": 0,
    "agree": 1,
    "strongly agree": 2,
}

IGNORED_RATINGS = {"n/a", "na"}  # Explicit non-scorable markers


def _normalize_rating(raw_rating: Any) -> Tuple[Optional[str], Optional[str]]:
    if not isinstance(raw_rating, str):
        return None, "missing or non-string rating"

    rating_str = raw_rating.strip().lower()
    if not rating_str:
        return None, "missing rating"

    cleaned = rating_str.replace("*", "").replace("_", "")
    cleaned = cleaned.replace("agrees", "agree").replace("agreed", "agree")
    cleaned = cleaned.replace("disagrees", "disagree").replace("disagreed", "disagree")
    cleaned = cleaned.rstrip(".! ")
    cleaned = " ".join(cleaned.split())

    if cleaned in IGNORED_RATINGS:
        return None, cleaned
    if cleaned.startswith("error:"):
        return None, cleaned  # Explicitly skip parser/judge errors

    return cleaned, None


def analyze_file(input_path: pathlib.Path) -> None:

    try:
        with input_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found: {input_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from file: {input_path}")
        return
    except Exception as e:
        print(f"Error reading file {input_path}: {e}")
        return

    results = data.get("results", [])
    if not results:
        print("Warning: No 'results' found in the input file.")
        return

    scores: List[int] = []
    refusal_ratings: Counter[str] = Counter()

    for i, result in enumerate(results):
        judge_rating = result.get("judge_rating")
        normalized_rating, skip_reason = _normalize_rating(judge_rating)
        numerical_score: Optional[int] = None

        if normalized_rating is not None:
            numerical_score = RATING_TO_SCORE.get(normalized_rating)
            if numerical_score is not None:
                scores.append(numerical_score)
                applied_rating = normalized_rating
            else:
                numerical_score = None
                refusal_ratings[f"unmapped rating '{normalized_rating}'"] += 1
                applied_rating = "- REFUSAL OR SAFETY"
        else:
            numerical_score = None
            refusal_ratings[skip_reason or "unmappable rating"] += 1
            applied_rating = "- REFUSAL OR SAFETY"

        # Persist normalized or fallback rating label
        if normalized_rating is not None and normalized_rating in RATING_TO_SCORE:
            result['judge_rating'] = normalized_rating
        else:
            result['judge_rating'] = applied_rating
        result['numerical_score'] = numerical_score

    average_score: Optional[float] = None
    total_score: Optional[int] = None
    if scores:
        average_score = statistics.mean(scores)
        total_score = sum(scores)
    else:
        print("  Warning: No valid scores found to calculate an average or sum.")

    if refusal_ratings:
        refusal_total = sum(refusal_ratings.values())
        details = "; ".join(f"{reason} ({count})" for reason, count in refusal_ratings.items())
        print(f"  Info: Marked {refusal_total} item(s) as '- REFUSAL OR SAFETY' with no score ({details}).")

    data['average_numerical_score'] = average_score
    data['total_numerical_score'] = total_score

    try:
        with input_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing updated file {input_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Analyze LLM experiment results and calculate numerical scores for judge ratings.")
    parser.add_argument(
        "input_files",
        metavar="FILE",
        type=pathlib.Path,
        nargs='+',
        help="Path(s) to the JSON result file(s) to analyze."
    )
    args = parser.parse_args()

    for file_path in args.input_files:
        analyze_file(file_path)
        print("---") # Separator between files

if __name__ == "__main__":
    main()
