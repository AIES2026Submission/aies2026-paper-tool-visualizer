import os
import json
import logging
import statistics
import pathlib
import time
import sys
from analyze_results import analyze_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def canonical_model_name(model_name: str, all_model_names: set) -> str:
    if not model_name:
        return model_name

    base_name = model_name.replace('_LATEST', '')
    if base_name != model_name and base_name in all_model_names:
        return base_name
    return model_name

def aggregate_results_for_dir(
    input_dir: pathlib.Path,
    output_file: pathlib.Path,
    file_pattern: str = '*.json'
):
    question_scores = {}
    refusal_counts = {}
    neutral_counts = {}
    rating_counts = {}
    question_order = []
    seen_questions = set()
    found_files = 0
    processed_files = 0

    logging.info(f"Processing directory: {input_dir} with pattern: {file_pattern}")
    for item in sorted(input_dir.glob(file_pattern)):
        if item.is_file():
            found_files += 1
            filename = item.name
            logging.debug(f"Processing file: {filename}")
            try:
                logging.debug(f"Running analyze_file on: {filename}")
                analyze_file(item)
                with open(item, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if 'results' in data and isinstance(data['results'], list):
                    scores_found_in_file = False
                    for result_item in data['results']:
                        if isinstance(result_item, dict) and 'question' in result_item and 'numerical_score' in result_item:
                            question = result_item['question']
                            score = result_item.get('numerical_score', None)
                            rating_label = (result_item.get('judge_rating') or "").strip().lower()

                            if question not in seen_questions:
                                seen_questions.add(question)
                                question_order.append(question)

                            if rating_label == "- refusal or safety":
                                refusal_counts[question] = refusal_counts.get(question, 0) + 1
                                scores_found_in_file = True
                                continue

                            if rating_label == "neutral":
                                neutral_counts[question] = neutral_counts.get(question, 0) + 1
                                scores_found_in_file = True
                                continue

                            if rating_label in ("strongly disagree", "disagree", "agree", "strongly agree"):
                                if question not in rating_counts:
                                    rating_counts[question] = {
                                        "strongly disagree": 0,
                                        "disagree": 0,
                                        "agree": 0,
                                        "strongly agree": 0,
                                    }
                                rating_counts[question][rating_label] += 1

                            if not isinstance(score, (int, float)):
                                logging.warning(f"Non-numeric score '{score}' found for question '{question}' in file {filename}. Skipping score.")
                                continue

                            if question not in question_scores:
                                question_scores[question] = []
                            question_scores[question].append(score)
                            scores_found_in_file = True
                        else:
                            logging.warning(f"Skipping invalid item in 'results' list in file: {filename}")

                    if scores_found_in_file:
                        processed_files += 1
                    else:
                       logging.warning(f"No valid score items found in file: {filename}")
                else:
                    logging.warning(f"'results' key missing or not a list in file: {filename}")

            except json.JSONDecodeError:
                logging.error(f"Error decoding JSON from file: {filename}")
            except Exception as e:
                logging.error(f"An unexpected error occurred processing file {filename}: {e}")

    if not question_scores and not refusal_counts and not neutral_counts:
        logging.warning(f"No score, neutral, or refusal data found in {input_dir}. Output file will not be created.")
        return False

    aggregated_stats = {}
    for question in question_order:
        scores = question_scores.get(question, [])
        try:
            count = len(scores)
            refusals = refusal_counts.get(question, 0)
            neutrals = neutral_counts.get(question, 0)
            total_responses = count + refusals + neutrals
            ratings = rating_counts.get(question, {
                "strongly disagree": 0,
                "disagree": 0,
                "agree": 0,
                "strongly agree": 0,
            })
            if scores:
                total = sum(scores)
                average = statistics.mean(scores)
                median = statistics.median(scores)
            else:
                total = 0
                average = 0
                median = 0

            aggregated_stats[question] = {
                'total_score': total,
                'average_score': average,
                'median_score': median,
                'count_scored': count,
                'neutral_count': neutrals,
                'refusal_count': refusals,
                'total_items': total_responses,
                'rating_counts': ratings
            }
        except statistics.StatisticsError as e:
             logging.error(f"Statistics error calculating stats for question '{question}' (scores: {scores}): {e}")
        except Exception as e:
            logging.error(f"Unexpected error calculating stats for question '{question}': {e}")

    if not aggregated_stats:
        logging.warning(f"Could not calculate statistics for any question in {input_dir}. Output file not created.")
        return False

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(aggregated_stats, f, indent=2, ensure_ascii=False)
        logging.info(f"Successfully aggregated statistics for {len(aggregated_stats)} unique questions from {processed_files}/{found_files} JSON files into: {output_file}")
        return True
    except Exception as e:
        logging.error(f"Failed to write aggregated data to {output_file}: {e}")
        return False

def main():
    logging.disable(logging.CRITICAL)
    PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()

    results_dir_candidates = (
        PROJECT_ROOT / "results",
        PROJECT_ROOT / "results" / "political_compass",
        PROJECT_ROOT.parent / "data",
    )

    base_results_dir = None
    for candidate in results_dir_candidates:
        if candidate.exists() and any((candidate / section).exists() for section in ("T1", "T2", "T3")):
            base_results_dir = candidate
            break
    if base_results_dir is None:
        base_results_dir = results_dir_candidates[0]

    base_output_dir = base_results_dir / "Aggregated Results"

    if not base_results_dir.is_dir():
        logging.error(f"Base results directory not found: {base_results_dir}")
        return

    try:
        base_output_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Ensured output directory exists: {base_output_dir}")
    except OSError as e:
        logging.error(f"Could not create base output directory {base_output_dir}: {e}")
        return

    total_processed_folders = 0
    successful_aggregations = 0

    all_model_names = set()
    for test_dir in base_results_dir.iterdir():
        if test_dir.is_dir() and test_dir.name.startswith('T'):
            for model_dir in test_dir.iterdir():
                if model_dir.is_dir():
                    all_model_names.add(model_dir.name)

    logging.info(f"Scanning base results directory: {base_results_dir}")
    aggregation_tasks = []
    for test_dir in base_results_dir.iterdir():
        if test_dir.is_dir() and test_dir.name.startswith('T'):
            logging.info(f"Scanning test directory: {test_dir.name} for model pair subdirectories...")
            found_model_pair_subdirs = False

            for model_pair_dir in test_dir.iterdir():
                if model_pair_dir.is_dir():
                    found_model_pair_subdirs = True
                    total_processed_folders += 1
                    canonical_name = canonical_model_name(model_pair_dir.name, all_model_names)
                    logging.info(f"Processing model pair directory: {model_pair_dir.name} (canonical: {canonical_name}) inside {test_dir.name}")

                    target_output_subdir = base_output_dir / canonical_name
                    target_output_subdir.mkdir(parents=True, exist_ok=True)

                    if test_dir.name == 'T3':
                        left_pattern = 'results_*_T3[-_]LEFT_*.json'
                        right_pattern = 'results_*_T3[-_]RIGHT_*.json'

                        left_output_filename = f"T3-LEFT_{canonical_name}_aggregated.json"
                        left_output_filepath = target_output_subdir / left_output_filename
                        aggregation_tasks.append((model_pair_dir, left_output_filepath, left_pattern))
                        logging.info(f"Aggregating T3-LEFT for {canonical_name} to {left_output_filepath}")

                        right_output_filename = f"T3-RIGHT_{canonical_name}_aggregated.json"
                        right_output_filepath = target_output_subdir / right_output_filename
                        aggregation_tasks.append((model_pair_dir, right_output_filepath, right_pattern))
                        logging.info(f"Aggregating T3-RIGHT for {canonical_name} to {right_output_filepath}")

                    elif test_dir.name == 'T1':
                        pattern = '*.json'
                        output_filename = f"T1_{canonical_name}_aggregated.json"
                        output_filepath = target_output_subdir / output_filename
                        aggregation_tasks.append((model_pair_dir, output_filepath, pattern))
                        logging.info(f"Aggregating T1 for {canonical_name} to {output_filepath}")

                    elif test_dir.name == 'T2':
                        left_pattern = '*_bias-left_*.json'
                        left_output_filename = f"T2-LEFT_{canonical_name}_aggregated.json"
                        left_output_filepath = target_output_subdir / left_output_filename
                        aggregation_tasks.append((model_pair_dir, left_output_filepath, left_pattern))
                        logging.info(f"Aggregating T2-LEFT for {canonical_name} to {left_output_filepath}")

                        right_pattern = '*_bias-right_*.json'
                        right_output_filename = f"T2-RIGHT_{canonical_name}_aggregated.json"
                        right_output_filepath = target_output_subdir / right_output_filename
                        aggregation_tasks.append((model_pair_dir, right_output_filepath, right_pattern))
                        logging.info(f"Aggregating T2-RIGHT for {canonical_name} to {right_output_filepath}")

                    else:
                        logging.warning(f"Unsupported test directory name '{test_dir.name}' for aggregation logic inside {model_pair_dir.name}. Skipping.")
                else:
                    logging.debug(f"Skipping non-directory item in {test_dir.name}: {model_pair_dir.name}")

            if not found_model_pair_subdirs:
                logging.warning(f"No subdirectories or relevant T3 files found to process within {test_dir.name}")
        else:
            logging.debug(f"Skipping non-test directory item in {base_results_dir}: {test_dir.name}")

    for input_dir, output_path, pattern in aggregation_tasks:
        if aggregate_results_for_dir(input_dir, output_path, pattern):
            successful_aggregations += 1

    print(f"{successful_aggregations} aggregated file(s) were successfully created in: {base_output_dir}.\nYou'll be returned to the main menu in two seconds.")
    time.sleep(2)
    sys.stdout.write('\033[F\033[K')
    sys.stdout.flush()


if __name__ == "__main__":
    main()
