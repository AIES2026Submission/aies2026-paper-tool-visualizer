#!/usr/bin/env python3
"""
Run Political Compass tests, normalize the results layout when needed, and rebuild the dashboard bundle.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List


REPO_ROOT = Path(__file__).resolve().parents[2]
VISUALIZER_ROOT = REPO_ROOT / "visualizer"
VISUALIZER_SCRIPTS_DIR = VISUALIZER_ROOT / "scripts"
AIDEOLOGY_ROOT = REPO_ROOT / "ai-deology"
SCRIPTS_DIR = AIDEOLOGY_ROOT / "scripts"
RESULTS_ROOT = AIDEOLOGY_ROOT / "results"
NESTED_RESULTS_ROOT = RESULTS_ROOT / "political_compass"
BUILD_SCRIPT = VISUALIZER_SCRIPTS_DIR / "build_data.py"


def run_cmd(cmd: List[str]) -> None:
    print(f"\n$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)


def build_model_args(args: argparse.Namespace) -> List[str]:
    model_args: List[str] = []

    if args.test_llm_id:
        model_args.extend(["--test-llm-id", args.test_llm_id])
    else:
        model_args.extend(["--test-llm-name", args.test_llm_name])

    if args.judge_llm_id:
        model_args.extend(["--judge-llm-id", args.judge_llm_id])
    else:
        model_args.extend(["--judge-llm-name", args.judge_llm_name])

    if args.num_questions is not None:
        model_args.extend(["--num-questions", str(args.num_questions)])

    if args.debug:
        model_args.append("--debug")

    return model_args


def sync_results(sync_mode: str) -> None:
    if sync_mode not in {"copy", "move"}:
        raise ValueError(f"Unsupported sync mode: {sync_mode}")

    if not NESTED_RESULTS_ROOT.exists():
        print("[SYNC] No nested ai-deology/results/political_compass tree found. Using ai-deology/results as-is.")
        return

    total_files = 0

    for section in ("T1", "T2", "T3", "Aggregated Results"):
        source_dir = NESTED_RESULTS_ROOT / section
        target_dir = RESULTS_ROOT / section

        if not source_dir.exists():
            print(
                "[WARN] Missing nested source section: "
                f"{source_dir}"
            )
            continue

        section_count = 0
        for source_file in source_dir.rglob("*.json"):
            rel_path = source_file.relative_to(source_dir)
            target_file = target_dir / rel_path
            target_file.parent.mkdir(parents=True, exist_ok=True)

            if sync_mode == "copy":
                shutil.copy2(source_file, target_file)
            else:
                if target_file.exists():
                    target_file.unlink()
                shutil.move(str(source_file), str(target_file))

            section_count += 1

        total_files += section_count
        verb = "copied" if sync_mode == "copy" else "moved"
        print(f"[SYNC] {section}: {section_count} file(s) {verb} to {target_dir}")

    verb = "copied" if sync_mode == "copy" else "moved"
    print(f"\n[SYNC COMPLETE] Total files {verb}: {total_files}")


def rebuild_dashboard_bundle() -> None:
    if not BUILD_SCRIPT.exists():
        print(f"[WARN] Missing dashboard build script: {BUILD_SCRIPT}")
        return

    print("\n[BUILD] Rebuilding visualizer/data.js")
    run_cmd([sys.executable, str(BUILD_SCRIPT)])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run llm_test1/2/3, normalize ai-deology/results when a nested "
            "political_compass layout exists, then rebuild visualizer/data.js."
        )
    )

    test_group = parser.add_mutually_exclusive_group(required=False)
    test_group.add_argument("--test-llm-id", type=str)
    test_group.add_argument("--test-llm-name", type=str)

    judge_group = parser.add_mutually_exclusive_group(required=False)
    judge_group.add_argument("--judge-llm-id", type=str)
    judge_group.add_argument("--judge-llm-name", type=str)

    parser.add_argument(
        "--num-questions",
        type=int,
        default=None,
        help="Optional question limit passed to all three scripts.",
    )
    parser.add_argument(
        "--sync-mode",
        choices=["copy", "move"],
        default="copy",
        help="How to flatten ai-deology/results/political_compass into ai-deology/results if needed.",
    )
    parser.add_argument(
        "--sync-only",
        action="store_true",
        help="Skip running tests; only normalize the results layout and rebuild the dashboard bundle.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip rebuilding visualizer/data.js after syncing.",
    )
    parser.add_argument("--debug", action="store_true")

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not AIDEOLOGY_ROOT.exists():
        print(f"[ERROR] Missing ai-deology root: {AIDEOLOGY_ROOT}")
        return 1

    model_args: List[str] = []

    if not args.sync_only:
        if not (args.test_llm_id or args.test_llm_name):
            print("[ERROR] Provide --test-llm-id or --test-llm-name (or use --sync-only).")
            return 1
        if not (args.judge_llm_id or args.judge_llm_name):
            print("[ERROR] Provide --judge-llm-id or --judge-llm-name (or use --sync-only).")
            return 1
        model_args = build_model_args(args)

    if not args.sync_only:
        run_cmd([sys.executable, str(SCRIPTS_DIR / "llm_test1.py"), "--test1", *model_args])
        run_cmd([sys.executable, str(SCRIPTS_DIR / "llm_test2.py"), "--bias-type", "both", *model_args])
        run_cmd(
            [
                sys.executable,
                str(SCRIPTS_DIR / "llm_test3.py"),
                "--test3",
                "--question-slant",
                "both",
                *model_args,
            ]
        )

    sync_results(args.sync_mode)
    if not args.skip_build:
        rebuild_dashboard_bundle()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
