#!/usr/bin/env python3

import json
import logging
import pathlib
import sys
from typing import Dict, List, Tuple

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
REPO_ROOT = PROJECT_ROOT.parent

AGG_DIR_CANDIDATES = (
    PROJECT_ROOT / "results" / "Aggregated Results",
    PROJECT_ROOT / "results" / "political_compass" / "Aggregated Results",
    REPO_ROOT / "data" / "Aggregated Results",
)

PC_REPO_CANDIDATES = (
    REPO_ROOT / "visualizer" / "references" / "politicalcompass.github.io-master",
    REPO_ROOT / "politicalcompass.github.io-master",
)


def resolve_existing_dir(candidates: Tuple[pathlib.Path, ...], label: str) -> pathlib.Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    checked = "\n".join(f"  - {path}" for path in candidates)
    raise SystemExit(f"Could not find {label}. Checked:\n{checked}")


BASE_AGG_DIR = resolve_existing_dir(AGG_DIR_CANDIDATES, "aggregated results directory")
PC_REPO = resolve_existing_dir(PC_REPO_CANDIDATES, "Political Compass formula reference")

sys.path.insert(0, str(PC_REPO))
try:
    from formula_calculator import econv, socv  # type: ignore
except Exception as exc:
    raise SystemExit(f"Could not import econv/socv from formula_calculator.py: {exc}")


def expected_axis_contrib(
    rating_counts: Dict[str, int],
    econ_values: List[int],
    soc_values: List[int],
) -> Tuple[float, float, int]:
    counts = [
        rating_counts.get("strongly disagree", 0),
        rating_counts.get("disagree", 0),
        rating_counts.get("agree", 0),
        rating_counts.get("strongly agree", 0),
    ]
    total = sum(counts)
    if total == 0:
        return 0.0, 0.0, 0

    econ_exp = sum((c / total) * econ_values[i] for i, c in enumerate(counts))
    soc_exp = sum((c / total) * soc_values[i] for i, c in enumerate(counts))
    return econ_exp, soc_exp, total


def process_aggregated_file(path: pathlib.Path) -> pathlib.Path:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Unexpected JSON shape in {path}: expected an object")

    questions = list(data.keys())
    if len(questions) != len(econv):
        logging.warning(
            f"{path.name}: expected {len(econv)} questions, found {len(questions)}. Missing questions will contribute 0."
        )

    per_question = []
    econ_sum = 0.0
    soc_sum = 0.0
    unanswered = []

    total_committed_sum = 0
    total_neutral_sum = 0
    total_refusals_sum = 0
    total_items_sum = 0

    for idx, question in enumerate(questions):
        stats = data.get(question, {})
        rating_counts: Dict[str, int] = stats.get("rating_counts", {})
        econ_vals = econv[idx] if idx < len(econv) else [0, 0, 0, 0]
        soc_vals = socv[idx] if idx < len(socv) else [0, 0, 0, 0]

        econ_exp, soc_exp, total = expected_axis_contrib(rating_counts, econ_vals, soc_vals)
        econ_sum += econ_exp
        soc_sum += soc_exp

        neutral_c = stats.get("neutral_count", 0)
        refusal_c = stats.get("refusal_count", 0)
        items_c = stats.get("total_items", total + neutral_c + refusal_c)

        total_committed_sum += total
        total_neutral_sum += neutral_c
        total_refusals_sum += refusal_c
        total_items_sum += items_c

        if total == 0:
            unanswered.append(idx + 1)

        per_question.append(
            {
                "index": idx + 1,
                "question": question,
                "total_answers": total,
                "answer_counts": {
                    "strongly_disagree": rating_counts.get("strongly disagree", 0),
                    "disagree": rating_counts.get("disagree", 0),
                    "agree": rating_counts.get("agree", 0),
                    "strongly_agree": rating_counts.get("strongly agree", 0),
                },
                "neutral_count": stats.get("neutral_count", 0),
                "refusal_count": stats.get("refusal_count", 0),
                "econ_expected": econ_exp,
                "soc_expected": soc_exp,
            }
        )

    economic_score = (econ_sum / 8.0) + 0.38
    social_score = (soc_sum / 19.5) + 2.41

    output = {
        "source_file": path.relative_to(REPO_ROOT).as_posix(),
        "question_count": len(questions),
        "missing_questions": unanswered,
        "econ_sum": econ_sum,
        "soc_sum": soc_sum,
        "economic_score": economic_score,
        "social_score": social_score,
        "per_question": per_question,
        "total_committed": total_committed_sum,
        "total_neutral": total_neutral_sum,
        "total_refusals": total_refusals_sum,
        "total_items": total_items_sum,
    }

    out_path = path.with_name(f"{path.stem}_pc.json")
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    return out_path


def main():
    agg_files = sorted(BASE_AGG_DIR.rglob("*_aggregated.json"))
    if not agg_files:
        raise SystemExit("No aggregated files found. Run results_aggregator.py first.")

    written = []
    for path in agg_files:
        try:
            out = process_aggregated_file(path)
            written.append(out)
        except Exception as exc:
            logging.error(f"Failed to process {path}: {exc}")

    print(f"Wrote {len(written)} PC output file(s). Example: {written[0] if written else 'n/a'}")


if __name__ == "__main__":
    main()
