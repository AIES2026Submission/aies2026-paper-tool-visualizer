import subprocess
import sys
import pathlib
import time
import os
import json
from collections import Counter
from datetime import datetime
import statistics
import textwrap

PROJECT_ROOT = pathlib.Path(__file__).parent.resolve()
DEFAULT_REQUEST_TIMEOUT_SECONDS = 15 * 60

SUPPORTED_MODELS = [
    # OpenAI
    "gpt-5.4",
    "gpt-5.4-mini",
    "gpt-5.4-nano",
    # Anthropic
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    # Google Gemini
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

IDEOLOGY_ART = "AI-DEOLOGY"

HEADER_HEIGHT = len(IDEOLOGY_ART.splitlines())

def clear_below_header():
    sys.stdout.write(f"\033[{HEADER_HEIGHT + 2};1H")
    sys.stdout.write("\033[J")
    sys.stdout.flush()


def sanitize_request_timeout_seconds(value):
    try:
        timeout_seconds = int(value)
    except (TypeError, ValueError):
        return DEFAULT_REQUEST_TIMEOUT_SECONDS
    if timeout_seconds <= 0:
        return DEFAULT_REQUEST_TIMEOUT_SECONDS
    return timeout_seconds


def format_timeout_seconds(timeout_seconds):
    timeout_seconds = sanitize_request_timeout_seconds(timeout_seconds)
    minutes, seconds = divmod(timeout_seconds, 60)
    if seconds == 0:
        unit = "minute" if minutes == 1 else "minutes"
        return f"{minutes} {unit}"
    if minutes == 0:
        unit = "second" if seconds == 1 else "seconds"
        return f"{seconds} {unit}"
    return f"{minutes}m {seconds}s"


def parse_timeout_input(raw_value):
    value = raw_value.strip().lower()
    if not value:
        raise ValueError("empty timeout")
    if value.endswith("ms"):
        raise ValueError("milliseconds are not supported")
    if value.endswith("m"):
        amount = int(value[:-1].strip())
        return sanitize_request_timeout_seconds(amount * 60)
    if value.endswith("s"):
        amount = int(value[:-1].strip())
        return sanitize_request_timeout_seconds(amount)
    amount = int(value)
    return sanitize_request_timeout_seconds(amount * 60)


def get_request_timeout_seconds(config):
    return sanitize_request_timeout_seconds(config.get("request_timeout_seconds", DEFAULT_REQUEST_TIMEOUT_SECONDS))

def select_model(prompt_message, config):
    print("Available Models:\n")
    model_data_map = {}
    index = 1
    for model in SUPPORTED_MODELS:
        print(f"{index}: {model} (api)")
        model_data_map[index] = model
        index += 1
    for name, cfg in config.get('custom_models', {}).items():
        mtype = cfg.get('type', 'local')
        print(f"{index}: {name} ({mtype})")
        model_data_map[index] = name
        index += 1
    back_option_index = index
    print(f"{back_option_index}: Back")
    while True:
        try:
            choice = input(f"\n{prompt_message} (enter number): ").strip()
            chosen_index = int(choice)
            if chosen_index == back_option_index:
                return None
            elif chosen_index in model_data_map:
                return model_data_map[chosen_index]
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except EOFError:
            print("\nInput stream closed unexpectedly. Exiting.")
            sys.exit(1)

def select_bias_type():
    print("\n--- Test 2 Bias Selection ---\n")
    print("  1: Left Bias History")
    print("  2: Right Bias History")
    print("  3: Both Left and Right Bias Histories")
    while True:
        try:
            choice = input("\nSelect the bias type for Test 2 (enter number 1, 2, or 3): ")
            choice_num = int(choice)
            if choice_num == 1:
                return 'left'
            elif choice_num == 2:
                return 'right'
            elif choice_num == 3:
                return 'both'
            else:
                print("Invalid number. Please enter 1, 2, or 3.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except EOFError:
             print("\nInput stream closed unexpectedly. Exiting.")
             sys.exit(1)

def select_slant_type():
    print("\n--- Test 3 Slant Selection ---\n")
    print("  1: Left Slanted Questions")
    print("  2: Right Slanted Questions")
    print("  3: Both Left and Right Slanted Questions")
    print("  4: Back")
    while True:
        try:
            choice = input("\nSelect the question slant for Test 3 (enter 1-4 or 'b' to go back): ").strip().lower()
            if choice in ('4', 'b', 'back'):
                return None
            choice_num = int(choice)
            if choice_num == 1:
                return 'left'
            elif choice_num == 2:
                return 'right'
            elif choice_num == 3:
                return 'both'
            else:
                print("Invalid number. Please enter 1, 2, 3, or 4 to go back.")
        except ValueError:
            print("Invalid input. Please enter a number or 'b'.")
        except EOFError:
             print("\nInput stream closed unexpectedly. Exiting.")
             sys.exit(1)

def prompt_run_count(prompt_message: str, default: int = 1) -> int:
    while True:
        try:
            runs_input = input(f"{prompt_message} (default {default}): ").strip()
            if not runs_input:
                return default
            runs = int(runs_input)
            if runs > 0:
                return runs
            print("Please enter a positive number.")
        except ValueError:
            print("Invalid input. Please enter a whole number.")
        except EOFError:
            print("\nInput stream closed unexpectedly. Exiting.")
            sys.exit(1)

def select_tests():
    print("\n--- Test Selection ---\n")
    print("  1: Test 1 = Original Political Compass Questions. No context added.")
    print("  2: Test 2 = Original Political Compass Questions. Simulated conversation with injected biais. Right, Left or both.")
    print("  3: Test 3 = Edited Political Compass Questions with Left and Right leaning biais (or both). No context added.")
    print("  4: All Tests (T1, T2, T3)")
    print("  5: Back to Main Menu")

    while True:
        try:
            choice = input("\nSelect the test(s) to run or go back (enter number 1-5): ")
            choice_num = int(choice)
            if choice_num == 5:
                return None, None, None
            elif 1 <= choice_num <= 4:
                run_t1 = (choice_num == 1 or choice_num == 4)
                run_t2 = (choice_num == 2 or choice_num == 4)
                run_t3 = (choice_num == 3 or choice_num == 4)
                return run_t1, run_t2, run_t3
            else:
                print("Invalid number. Please enter a number between 1 and 5.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except EOFError:
             print("\nInput stream closed unexpectedly. Exiting.")
             sys.exit(1)

def run_aggregator():
    clear_below_header()
    print("\n--- Result Aggregation ---\n")
    script_dir = PROJECT_ROOT
    aggregator_script = script_dir / "scripts" / "results_aggregator.py"
    converter_script = script_dir / "scripts" / "pc_converter.py"

    bar_length = 30
    duration = 2.0
    for i in range(bar_length + 1):
        filled = '#' * i
        empty = ' ' * (bar_length - i)
        print(f"\r[{filled}{empty}]", end='', flush=True)
        time.sleep(duration / bar_length)
    print(" ✓")

    try:
        subprocess.run([sys.executable, str(aggregator_script)], check=True, text=True, cwd=script_dir, capture_output=False)
        subprocess.run([sys.executable, str(converter_script)], check=True, text=True, cwd=script_dir, capture_output=False)
    except FileNotFoundError:
        print(f"\nError: Could not find one of the aggregation scripts in {script_dir / 'scripts'}.")
    except subprocess.CalledProcessError as e:
        print(f"\nError: Aggregation pipeline exited with an error (code {e.returncode}).")
        print("--- Pipeline Output ---")
        print(e.stdout)
        print(e.stderr)
        print("-----------------------")
    except Exception as e:
        print(f"\nAn unexpected error occurred during aggregation/conversion: {e}")

def show_settings_menu(current_num_questions, config):
    while True:
        clear_below_header()
        print("\n--- Settings ---\n")
        print("1. Number of questions per test")
        print(f"2. Response timeout per answer ({format_timeout_seconds(get_request_timeout_seconds(config))})")
        print("3. Custom Models")
        print("4. Back to main menu")
        choice = input("\nEnter your choice (1-4): ").strip()
        if choice == '1':
            current_num_questions = show_num_questions_menu(current_num_questions)
        elif choice == '2':
            show_request_timeout_menu(config)
        elif choice == '3':
            show_custom_models_menu(config)
        elif choice == '4':
            return current_num_questions
        else:
            print("Invalid choice. Please try again.")


def show_request_timeout_menu(config):
    while True:
        clear_below_header()
        current_timeout_seconds = get_request_timeout_seconds(config)
        print("\n--- Response Timeout ---\n")
        print(f"Current timeout per answer: {format_timeout_seconds(current_timeout_seconds)} ({current_timeout_seconds} seconds)")
        print("\n1. Change timeout")
        print("2. Back to settings")
        choice = input("\nEnter your choice (1-2): ").strip()
        if choice == '1':
            raw_timeout = input("\nEnter new timeout in minutes (e.g. 15), or use '900s' / '15m': ").strip().lower()
            try:
                new_timeout_seconds = parse_timeout_input(raw_timeout)
            except ValueError:
                print("Invalid timeout. Use a positive number, optionally ending with 'm' or 's'.")
                time.sleep(1)
                continue
            config["request_timeout_seconds"] = new_timeout_seconds
            save_config(config)
            print(f"Response timeout set to {format_timeout_seconds(new_timeout_seconds)}.")
            time.sleep(1)
            return
        elif choice == '2':
            return
        else:
            print("Invalid choice. Please try again.")
            time.sleep(1)

def show_num_questions_menu(current_num_questions):
    while True:
        clear_below_header()
        print("\n--- Number of Questions ---\n")
        print(f"Current number of questions per test: {'All' if current_num_questions is None else current_num_questions}")
        print("\n1. Change number of questions")
        print("2. Back to settings")
        choice = input("\nEnter your choice (1-2): ").strip()
        if choice == '1':
            q_choice = input("\nEnter new number of questions (e.g., 5, 10) or 'all': ").strip().lower()
            if q_choice in ('all', ''):
                current_num_questions = None
                print("Number of questions set to All.")
            else:
                try:
                    num = int(q_choice)
                    if num > 0:
                        current_num_questions = num
                        print(f"Number of questions set to {num}.")
                    else:
                        print("Number must be positive.")
                except ValueError:
                    print("Invalid number.")
            return current_num_questions
        elif choice == '2':
            return current_num_questions
        else:
            print("Invalid choice. Please try again.")

def show_custom_models_menu(config):
    while True:
        clear_below_header()
        print("\n--- Custom Models ---")
        custom_models = config.get('custom_models', {})
        if not custom_models:
            print("   (No custom models configured)")
        else:
            for i, (model_name, model_cfg) in enumerate(custom_models.items()):
                print(f"  {i + 1}: {model_name} ({model_cfg.get('type', 'Unknown Type')})")
        print("\n1. Add Custom Model")
        print("2. Remove Custom Model")
        print("3. Back")
        choice = input("\nEnter your choice (1-3): ").strip()
        if choice == '1':
            add_custom_model(config)
            save_config(config)
        elif choice == '2':
            remove_custom_model(config)
            save_config(config)
        elif choice == '3':
            break
        else:
            print("Invalid choice. Please try again.")

def add_custom_model(config):
    print("\n--- Add Custom Model ---")
    model_type = input("Model type ('api' or 'local'): ").strip().lower()
    if model_type not in ['api', 'local']:
        print("Invalid type.")
        return

    model_name = input("Display Name for the model: ").strip()
    if not model_name:
        print("Model name cannot be empty.")
        return

    new_model = {"name": model_name, "type": model_type}

    if model_type == 'api':
        model_id = input("Model ID (e.g., 'gpt-5.4-mini', 'claude-sonnet-4-6', 'gemini-2.5-flash'): ").strip()
        endpoint = input("API Endpoint URL (leave blank if not needed): ").strip()
        api_key_env = input("Environment variable name for API Key (e.g., 'OPENAI_API_KEY'): ").strip()
        if not model_id or not api_key_env:
            print("API Model ID and API Key Environment Variable are required.")
            return
        new_model['id'] = model_id
        if endpoint:
            new_model['endpoint'] = endpoint
        new_model['api_key_env'] = api_key_env

    elif model_type == 'local':
        model_identifier = input("Local model identifier (e.g., path or known name): ").strip()
        if not model_identifier:
            print("Local model identifier is required.")
            return
        new_model['identifier'] = model_identifier

    if 'custom_models' not in config:
        config['custom_models'] = {}

    if any(m.get('name') == model_name for m in config['custom_models'].values()):
        print(f"A custom model named '{model_name}' already exists.")
        return

    config['custom_models'][model_name] = new_model
    print(f"Custom model '{model_name}' added.")

def remove_custom_model(config):
    print("\n--- Remove Custom Model ---")
    custom_models = config.get('custom_models', {})
    if not custom_models:
        print("No custom models to remove.")
        return

    print("Configured Custom Models:")
    for i, (model_name, model_cfg) in enumerate(custom_models.items()):
        print(f"  {i + 1}: {model_name} ({model_cfg.get('type', 'Unknown Type')})")

    while True:
        try:
            choice = input("Enter the number of the model to remove (or 'b' to go back): ").strip().lower()
            if choice == 'b':
                return
            index = int(choice) - 1
            if 0 <= index < len(custom_models):
                removed_model = list(custom_models.keys())[index]
                print(f"Removed model: {removed_model}")
                del config['custom_models'][removed_model]
                return
            else:
                print("Invalid number.")
        except ValueError:
            print("Invalid input. Please enter a number or 'b'.")

CONFIG_FILE = PROJECT_ROOT / "config.json"
RESULTS_DIR_CANDIDATES = (
    PROJECT_ROOT / "results",
    PROJECT_ROOT / "results" / "political_compass",
)


def resolve_results_base_dir():
    preferred = RESULTS_DIR_CANDIDATES[0]
    for candidate in RESULTS_DIR_CANDIDATES:
        if not candidate.exists():
            continue
        if any((candidate / section).exists() for section in ("T1", "T2", "T3", "Aggregated Results")):
            return candidate
    for candidate in RESULTS_DIR_CANDIDATES:
        if candidate.exists():
            return candidate
    return preferred

def load_config():
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open('r', encoding='utf-8') as f:
                config = json.load(f)
                if 'custom_models' not in config or not isinstance(config['custom_models'], dict):
                    config['custom_models'] = {}
                config['request_timeout_seconds'] = get_request_timeout_seconds(config)
                return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"\nWarning: Could not load {CONFIG_FILE}. Using defaults. Error: {e}")
            return {"custom_models": {}, "request_timeout_seconds": DEFAULT_REQUEST_TIMEOUT_SECONDS}
    return {"custom_models": {}, "request_timeout_seconds": DEFAULT_REQUEST_TIMEOUT_SECONDS}

def save_config(config):
    try:
        with CONFIG_FILE.open('w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except IOError as e:
        print(f"\nError: Could not save configuration to {CONFIG_FILE}. Error: {e}")

current_config = load_config()

def format_file_size(num_bytes):
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != 'B' else f"{int(size)} {unit}"
        size /= 1024

def format_timestamp(ts):
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError):
        return "Unknown"

def summarize_test_run(data):
    results = [entry for entry in data.get('results', []) if isinstance(entry, dict)]
    total_questions = len(results)
    print(f"Questions answered : {total_questions}")
    if not results:
        return

    judge = data.get('judge_llm_model', 'Unknown Judge')
    tested = data.get('test_llm_model', 'Unknown Test Model')
    test_id = data.get('test_id') or results[0].get('test_type', 'Unknown Test')
    print(f"Test ID          : {test_id}")
    print(f"Test LLM         : {tested}")
    print(f"Judge LLM        : {judge}")

    rating_counts = Counter()
    for entry in results:
        rating = entry.get('judge_rating') or 'unrated'
        rating_counts[rating] += 1
    print("\nJudge Ratings:")
    for rating, count in rating_counts.most_common():
        print(f"  - {rating}: {count}")

    scores = [entry.get('numerical_score') for entry in results if isinstance(entry.get('numerical_score'), (int, float))]
    if scores:
        try:
            avg_score = statistics.mean(scores)
            median_score = statistics.median(scores)
            min_score = min(scores)
            max_score = max(scores)
            print("\nScore Stats:")
            print(f"  Avg: {avg_score:.2f}   Median: {median_score:.2f}   Min: {min_score:.2f}   Max: {max_score:.2f}")
        except statistics.StatisticsError:
            pass

    sample_count = min(3, total_questions)
    if sample_count:
        print("\nSample Questions:")
        for entry in results[:sample_count]:
            idx = entry.get('question_index', '?')
            question = entry.get('question', '').strip()
            question_flat = ' '.join(question.split())
            wrapped_question = textwrap.fill(
                question_flat,
                width=90,
                initial_indent='    ',
                subsequent_indent='    '
            )
            rating = entry.get('judge_rating', 'unrated')
            score = entry.get('numerical_score', 'n/a')
            print(f"- Q{idx} | Rating: {rating} | Score: {score}")
            print(wrapped_question)

def summarize_aggregated_results(data):
    if not isinstance(data, dict):
        print("File format not recognized for aggregation summary.")
        return

    stats_entries = [
        (question, values) for question, values in data.items()
        if isinstance(values, dict) and any(k in values for k in ('average_score', 'median_score', 'count'))
    ]

    if not stats_entries:
        preview = json.dumps(data, indent=2)
        if len(preview) > 1200:
            preview = preview[:1200] + "\n... (truncated)"
        print("File Preview:\n")
        print(preview)
        return

    print(f"Questions aggregated : {len(stats_entries)}")
    avg_scores = [
        val.get('average_score') for _, val in stats_entries
        if isinstance(val.get('average_score'), (int, float))
    ]
    if avg_scores:
        try:
            print(f"Average of averages : {statistics.mean(avg_scores):.2f}")
            print(f"Median of averages  : {statistics.median(avg_scores):.2f}")
        except statistics.StatisticsError:
            pass

    top_entries = sorted(
        stats_entries,
        key=lambda item: abs(item[1].get('average_score', 0)),
        reverse=True
    )[:3]

    if top_entries:
        print("\nTop magnitude questions:")
        for question, values in top_entries:
            avg = values.get('average_score', 'n/a')
            med = values.get('median_score', 'n/a')
            count = values.get('count', 'n/a')
            wrapped_question = textwrap.fill(
                ' '.join(question.split()),
                width=90,
                initial_indent='    ',
                subsequent_indent='    '
            )
            print(f"- Avg: {avg} | Median: {med} | Samples: {count}")
            print(wrapped_question)

def display_result_file(file_path):
    while True:
        clear_below_header()
        rel_path = file_path
        try:
            rel_path = file_path.relative_to(pathlib.Path(__file__).parent)
        except ValueError:
            pass

        print("\n--- Result Preview ---\n")
        print(f"File     : {rel_path}")
        try:
            stats = file_path.stat()
            print(f"Modified : {format_timestamp(stats.st_mtime)}")
            print(f"Size     : {format_file_size(stats.st_size)}")
        except FileNotFoundError:
            print("File no longer exists on disk.")
            input("\nPress Enter to return...")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"\nError: Could not parse JSON ({exc}).")
            input("\nPress Enter to return...")
            return
        except OSError as exc:
            print(f"\nError reading file: {exc}")
            input("\nPress Enter to return...")
            return

        if isinstance(data, dict) and 'results' in data:
            summarize_test_run(data)
        else:
            summarize_aggregated_results(data)

        action = input("\nPress Enter to go back or type 'v' for a JSON preview: ").strip().lower()
        if action == 'v':
            preview = json.dumps(data, indent=2)
            if len(preview) > 4000:
                preview = preview[:4000] + "\n... (truncated)"
            print("\n--- JSON Preview ---\n")
            print(preview)
            input("\nPress Enter to return to the summary...")
        else:
            return

def select_result_file(test_label, model_label, model_path):
    while True:
        clear_below_header()
        print(f"\n--- {test_label} / {model_label} ---\n")
        files = [
            f for f in sorted(model_path.glob('*.json'), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
            if f.is_file()
        ]

        if not files:
            print("No JSON result files found in this directory.")
            input("\nPress Enter to go back...")
            return

        for idx, file in enumerate(files, start=1):
            try:
                stats = file.stat()
                timestamp = format_timestamp(stats.st_mtime)
                size = format_file_size(stats.st_size)
            except FileNotFoundError:
                timestamp = "Unknown"
                size = "Unknown"
            print(f"{idx}: {file.name} ({timestamp}, {size})")
        print("B: Back")

        choice = input("\nSelect a result file: ").strip().lower()
        if choice == 'b':
            return
        try:
            file_index = int(choice) - 1
            if 0 <= file_index < len(files):
                display_result_file(files[file_index])
            else:
                print("Invalid selection. Try again.")
                time.sleep(1)
        except ValueError:
            print("Invalid input. Please enter a number or 'B'.")
            time.sleep(1)

def select_model_directory(test_label, test_path):
    while True:
        clear_below_header()
        print(f"\n--- {test_label} Results ---\n")
        entries = []
        index = 1

        subdirs = [d for d in sorted(test_path.iterdir()) if d.is_dir()]
        for directory in subdirs:
            json_count = len(list(directory.glob('*.json')))
            print(f"{index}: {directory.name} ({json_count} files)")
            entries.append(('dir', directory))
            index += 1

        root_files = [f for f in sorted(test_path.glob('*.json')) if f.is_file()]
        for file in root_files:
            try:
                file_size = format_file_size(file.stat().st_size)
            except FileNotFoundError:
                file_size = "Unknown size"
            print(f"{index}: {file.name} ({file_size})")
            entries.append(('file', file))
            index += 1

        if not entries:
            print("No result data found for this test yet.")
            input("\nPress Enter to go back...")
            return

        print("B: Back")
        choice = input("\nSelect a model directory or file: ").strip().lower()
        if choice == 'b':
            return
        try:
            selection = int(choice) - 1
            if 0 <= selection < len(entries):
                entry_type, path_obj = entries[selection]
                if entry_type == 'dir':
                    select_result_file(test_label, path_obj.name, path_obj)
                else:
                    display_result_file(path_obj)
            else:
                print("Invalid selection. Try again.")
                time.sleep(1)
        except ValueError:
            print("Invalid input. Please enter a number or 'B'.")
            time.sleep(1)

def view_results():
    while True:
        clear_below_header()
        print("\n--- Result Browser ---\n")
        results_base_dir = resolve_results_base_dir()
        if not results_base_dir.exists():
            print(f"No results directory found at:\n{results_base_dir}")
            input("\nRun a test first, then press Enter to return to the menu...")
            return

        test_dirs = [
            d for d in sorted(results_base_dir.iterdir())
            if d.is_dir()
        ]

        if not test_dirs:
            print("No test runs have been recorded yet.")
            input("\nPress Enter to go back...")
            return

        for idx, directory in enumerate(test_dirs, start=1):
            model_count = len([d for d in directory.iterdir() if d.is_dir()])
            print(f"{idx}: {directory.name} ({model_count} model folders)")
        print("B: Back to main menu")

        choice = input("\nSelect a test directory: ").strip().lower()
        if choice == 'b':
            return
        try:
            selection = int(choice) - 1
            if 0 <= selection < len(test_dirs):
                selected_dir = test_dirs[selection]
                select_model_directory(selected_dir.name, selected_dir)
            else:
                print("Invalid selection. Try again.")
                time.sleep(1)
        except ValueError:
            print("Invalid input. Please enter a number or 'B'.")
            time.sleep(1)

def run_tests(num_questions=None, config=None):
    clear_below_header()
    request_timeout_seconds = get_request_timeout_seconds(config or {})
    run_t1, run_t2, run_t3 = select_tests()

    if run_t1 is None and run_t2 is None and run_t3 is None:
         return

    clear_below_header()
    print("\n--- Test LLM Selection ---\n")
    test_model = select_model("Select the Test LLM", config)
    if test_model is None:
        return

    clear_below_header()
    print("\n--- Judge LLM Selection ---\n")
    judge_model = select_model("Select the Judge LLM", config)
    if judge_model is None:
        return

    bias_type_t2 = None
    slant_types_t3 = []

    script_dir = pathlib.Path(__file__).parent.resolve()
    commands_to_run = []

    if run_t1 and run_t2 and run_t3:
        clear_below_header()

        num_runs = prompt_run_count("\nEnter number of times to run all tests", default=1)

        clear_below_header()
        print("\n--- Ready to Run --- \n")
        print(f"Test LLM:  {test_model}")
        print(f"Judge LLM: {judge_model}")
        print(f"Tests:     All (T1, T2, T3)")
        print(f"Runs:      {num_runs}")
        print(f"Timeout:   {format_timeout_seconds(request_timeout_seconds)}")
        if num_questions is not None:
             print(f"Questions: First {num_questions}")
        print("----------------------")

        confirm = input("\nProceed with these settings? (y/n): ").lower()
        if confirm != 'y':
            print("Aborted by user.")
            return

        clear_below_header()

        all_tests_script = script_dir / "scripts" / "llm_test_all.py"
        cmd_all = [
            sys.executable, str(all_tests_script),
        ]
        if test_model in config.get('custom_models', {}):
            cmd_all.extend(['--test-llm-name', test_model])
        else:
            cmd_all.extend(['--test-llm-id', test_model])

        if judge_model in config.get('custom_models', {}):
            cmd_all.extend(['--judge-llm-name', judge_model])
        else:
            cmd_all.extend(['--judge-llm-id', judge_model])

        cmd_all.extend(['--runs', str(num_runs)])
        cmd_all.extend(['--request-timeout-seconds', str(request_timeout_seconds)])
        if num_questions is not None:
            cmd_all.extend(['--num-questions', str(num_questions)])
        commands_to_run.append(cmd_all)

    else:
        if run_t2:
            clear_below_header()
            bias_type_t2 = select_bias_type()
            if bias_type_t2 is None: return

        if run_t3:
            if not run_t2 or bias_type_t2 is None:
                 clear_below_header()
            slant_choice = select_slant_type()
            if slant_choice is None:
                return
            if slant_choice == 'both':
                slant_types_t3 = ['left', 'right']
            else:
                slant_types_t3 = [slant_choice]

        num_runs_selected = prompt_run_count("\nEnter number of times to run the selected tests", default=1)

        clear_below_header()
        print("\n--- Ready to Run --- \n")
        print(f"Test LLM:  {test_model}")
        print(f"Judge LLM: {judge_model}")
        selected_tests_str = []
        if run_t1: selected_tests_str.append("T1")
        if run_t2: selected_tests_str.append("T2")
        if run_t3: selected_tests_str.append("T3")
        print(f"Tests:     {' '.join(selected_tests_str)}")
        if run_t2 and bias_type_t2:
            print(f"T2 Bias:   {bias_type_t2.capitalize()}")
        if run_t3 and slant_types_t3:
            if len(slant_types_t3) == 2:
                print("T3 Slant:  Left + Right")
            else:
                print(f"T3 Slant:  {slant_types_t3[0].capitalize()}")
        print(f"Runs:      {num_runs_selected}")
        print(f"Timeout:   {format_timeout_seconds(request_timeout_seconds)}")
        if num_questions is not None:
            print(f"Questions: First {num_questions}")
        print("----------------------")

        confirm = input("\nProceed with these settings? (y/n): ").lower()
        if confirm != 'y':
            print("Aborted by user.")
            return

        clear_below_header()

        single_run_commands = []
        if run_t1:
            test1_script = script_dir / "scripts" / "llm_test1.py"
            cmd_t1 = [
                sys.executable,
                str(test1_script),
                '--test1',
            ]
            if test_model in config.get('custom_models', {}):
                cmd_t1.extend(['--test-llm-name', test_model])
            else:
                cmd_t1.extend(['--test-llm-id', test_model])

            if judge_model in config.get('custom_models', {}):
                cmd_t1.extend(['--judge-llm-name', judge_model])
            else:
                cmd_t1.extend(['--judge-llm-id', judge_model])

            cmd_t1.extend(['--request-timeout-seconds', str(request_timeout_seconds)])
            if num_questions is not None:
                cmd_t1.extend(['--num-questions', str(num_questions)])
            single_run_commands.append(cmd_t1)

        if run_t2 and bias_type_t2:
            test2_script = script_dir / "scripts" / "llm_test2.py"
            cmd_t2 = [
                sys.executable,
                str(test2_script),
                '--bias-type', bias_type_t2
            ]
            if test_model in config.get('custom_models', {}):
                cmd_t2.extend(['--test-llm-name', test_model])
            else:
                cmd_t2.extend(['--test-llm-id', test_model])

            if judge_model in config.get('custom_models', {}):
                cmd_t2.extend(['--judge-llm-name', judge_model])
            else:
                cmd_t2.extend(['--judge-llm-id', judge_model])

            cmd_t2.extend(['--request-timeout-seconds', str(request_timeout_seconds)])
            if num_questions is not None:
                cmd_t2.extend(['--num-questions', str(num_questions)])
            single_run_commands.append(cmd_t2)

        if run_t3 and slant_types_t3:
            for slant_value in slant_types_t3:
                test3_script = script_dir / "scripts" / "llm_test3.py"
                cmd_t3 = [
                    sys.executable,
                    str(test3_script),
                    '--test3',
                    '--question-slant', slant_value
                ]
                if test_model in config.get('custom_models', {}):
                    cmd_t3.extend(['--test-llm-name', test_model])
                else:
                    cmd_t3.extend(['--test-llm-id', test_model])

                if judge_model in config.get('custom_models', {}):
                    cmd_t3.extend(['--judge-llm-name', judge_model])
                else:
                    cmd_t3.extend(['--judge-llm-id', judge_model])
                cmd_t3.extend(['--request-timeout-seconds', str(request_timeout_seconds)])
                if num_questions is not None:
                    cmd_t3.extend(['--num-questions', str(num_questions)])
                single_run_commands.append(cmd_t3)

        if not single_run_commands:
            print("No tests were configured to run. Returning to menu.")
            return

        for _ in range(num_runs_selected):
            for cmd in single_run_commands:
                commands_to_run.append(cmd.copy())

    start_time = time.time()
    total_commands = len(commands_to_run)
    for i, command in enumerate(commands_to_run):
        script_name = pathlib.Path(command[1]).name
        try:
            process = subprocess.Popen(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=script_dir)
            for line in process.stdout:
                 sys.stdout.write(line)
                 sys.stdout.flush()
            process.wait()
            if process.returncode != 0:
                 print(f"\nError: {script_name} exited with code {process.returncode}")
        except FileNotFoundError:
            print(f"Error: Could not find {command[1]}. Make sure it's in the scripts directory.")
        except Exception as e:
            print(f"An unexpected error occurred while running {script_name}: {e}")

    end_time = time.time()
    print(f"\n--- All selected tests finished in {end_time - start_time:.2f} seconds. ---")
    print("\nReturning to main menu in 3 seconds...")
    time.sleep(3)

def main_menu(num_questions_setting):
    clear_below_header()
    print("\n--- Main Menu ---\n")
    print("  1: Run Tests")
    print("  2: View Results")
    print("  3: Aggregate Results")
    print("  4: Settings")
    print("  5: Exit\n")
    print("-" * 30)

    choice = input("\nEnter your choice (1-5): ")
    return choice

def main():
    for char in IDEOLOGY_ART:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.0005)
    print()

    num_questions = None

    while True:
        choice = main_menu(num_questions)

        if choice == '1':
            run_tests(num_questions=num_questions, config=current_config)
        elif choice == '2':
            view_results()
        elif choice == '3':
            run_aggregator()
        elif choice == '4':
             num_questions = show_settings_menu(num_questions, current_config)
        elif choice == '5':
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 5.")
            time.sleep(1)

if __name__ == "__main__":
    main()
