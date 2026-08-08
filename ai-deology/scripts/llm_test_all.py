import argparse
import os
import subprocess
import sys
import pathlib
from analyze_results import analyze_file
import time

from logging_utils import DebugLogger, is_debug_enabled, DEBUG_ENV_VAR

LOGGER = DebugLogger("llm_test_all")

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

SCRIPT_TEST1 = SCRIPTS_DIR / "llm_test1.py"
SCRIPT_TEST2 = SCRIPTS_DIR / "llm_test2.py"
SCRIPT_TEST3 = SCRIPTS_DIR / "llm_test3.py"

def main(args):
    LOGGER.info(f"Starting 'all_tests' run sequence with args: {args}")
    print(f"\nStarting 'all_tests' run sequence.")
    # Display the chosen models clearly
    test_model_arg = f"--test-llm-id {args.test_llm_id}" if args.test_llm_id else f"--test-llm-name '{args.test_llm_name}'"
    judge_model_arg = f"--judge-llm-id {args.judge_llm_id}" if args.judge_llm_id else f"--judge-llm-name '{args.judge_llm_name}'"
    print(f"  Test LLM: {test_model_arg}")
    print(f"  Judge LLM: {judge_model_arg}")
    print(f"  Number of Runs: {args.runs}")
    if args.num_questions is not None:
        print(f"  Number of Questions: {args.num_questions}")
    print(f"  Request Timeout: {args.request_timeout_seconds} seconds")
    print("-" * 40)

    start_time_all = time.time()
    all_runs_successful = True

    for run_num in range(1, args.runs + 1):
        LOGGER.info(f"Run {run_num}/{args.runs} starting")
        print(f"\n=== Starting Run {run_num}/{args.runs} ===")
        start_time_run = time.time()
        run_successful = True

        def execute_test(command: list, script_name: str):
            nonlocal run_successful # Allow modification of the outer scope variable
            print(f"\n  Preparing to run: {script_name}")
            print(f"    Executing command list: {command}") # Print the exact list
            LOGGER.info(f"Run {run_num}/{args.runs} -> launching {script_name}: {' '.join(command)}")
            try:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, # Merge stderr into stdout
                    text=True, # Decode output as text
                    cwd=PROJECT_ROOT,
                    bufsize=1, # Line buffered
                    universal_newlines=True # Ensure cross-platform newline handling
                )

                print(f"\n--- {script_name} output ---")
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    sys.stdout.write(f"      | {line.rstrip()}\n") # Indent sub-script output clearly
                    sys.stdout.flush()

                process.wait()
                LOGGER.info(f"{script_name} finished with exit code {process.returncode}")

                print(f"--- end {script_name} output ---")

                if process.returncode == 0:
                    print(f"    --> {script_name} completed successfully (Exit Code 0).")
                    LOGGER.debug(f"{script_name} succeeded")
                    return True
                else:
                    print(f"\n    --> Error: {script_name} exited with code {process.returncode}")
                    print("    " + "-" * 30)
                    run_successful = False
                    LOGGER.error(f"{script_name} exited with code {process.returncode}")
                    return False

            except FileNotFoundError:
                print(f"Error: Script not found at {command[1]}")
                run_successful = False
                LOGGER.error(f"Script not found: {command[1]}")
                return False
            except Exception as e:
                 print(f"An unexpected error occurred running {script_name}: {e}")
                 run_successful = False
                 LOGGER.exception(e, context=f"Unexpected error in {script_name}")
                 return False

        # --- Common arguments for all tests ---
        common_args = []
        if args.test_llm_id:
            common_args.extend(['--test-llm-id', args.test_llm_id])
        else:
            common_args.extend(['--test-llm-name', args.test_llm_name])

        if args.judge_llm_id:
            common_args.extend(['--judge-llm-id', args.judge_llm_id])
        else:
            common_args.extend(['--judge-llm-name', args.judge_llm_name])

        if args.num_questions is not None:
            common_args.extend(['--num-questions', str(args.num_questions)])
        common_args.extend(['--request-timeout-seconds', str(args.request_timeout_seconds)])

        # --- Test 1 ---
        print("\n[Test 1: Original Questions]")
        cmd_t1 = [
            sys.executable, str(SCRIPT_TEST1),
            '--test1'       # Use the correct flag for llm_test1.py
        ]
        cmd_t1.extend(common_args)
        execute_test(cmd_t1, SCRIPT_TEST1.name)

        # --- Test 2: Bias Injection ---
        # Left
        if run_successful:
            print("\n[Test 2: Bias Injection - Left History]")
            cmd_t2_left = [
                sys.executable, str(SCRIPT_TEST2),
                '--bias-type', 'left'
            ]
            cmd_t2_left.extend(common_args)
            execute_test(cmd_t2_left, SCRIPT_TEST2.name)
        # Right
        if run_successful:
            print("\n[Test 2: Bias Injection - Right History]")
            cmd_t2_right = [
                sys.executable, str(SCRIPT_TEST2),
                '--bias-type', 'right'
            ]
            cmd_t2_right.extend(common_args)
            execute_test(cmd_t2_right, SCRIPT_TEST2.name)

        # --- Test 3: Slanted Questions ---
        # Left
        if run_successful:
            print("\n[Test 3: Slanted Questions - Left]")
            cmd_t3_left = [
                sys.executable, str(SCRIPT_TEST3),
                '--test3', '--question-slant', 'left'  # Use the flags for llm_test3.py
            ]
            cmd_t3_left.extend(common_args)
            execute_test(cmd_t3_left, SCRIPT_TEST3.name)
        # Right
        if run_successful:
            print("\n[Test 3: Slanted Questions - Right]")
            cmd_t3_right = [
                sys.executable, str(SCRIPT_TEST3),
                '--test3', '--question-slant', 'right'  # Use the flags for llm_test3.py
            ]
            cmd_t3_right.extend(common_args)
            execute_test(cmd_t3_right, SCRIPT_TEST3.name)

        end_time_run = time.time()
        print(f"\n--- Run {run_num} finished in {end_time_run - start_time_run:.2f} seconds. ---")
        if not run_successful:
            print(f"!!! Run {run_num} encountered errors. See output above. !!!")
            all_runs_successful = False
            # break
        LOGGER.info(f"Run {run_num}/{args.runs} finished (success={run_successful})")

    end_time_all = time.time()
    print(f"\n{'='*15} All {args.runs} runs completed in {end_time_all - start_time_all:.2f} seconds. {'='*15}")
    if not all_runs_successful:
        print("!!! One or more runs encountered errors. !!!")
        # sys.exit(1)
        LOGGER.warning("One or more runs encountered errors.")

    print("\n--- Analyzing all result JSON files ---")
    results_dir = PROJECT_ROOT / "results"
    for json_file in results_dir.rglob("*.json"):
        if "Aggregated Results" in json_file.parts or json_file.name.endswith("_pc.json") or json_file.name.endswith("_aggregated.json"):
            continue
        try:
            analyze_file(json_file)
            print(f"Analyzed: {json_file}")
            LOGGER.debug(f"Analyzed result file: {json_file}")
        except Exception as e:
            print(f"Error analyzing {json_file}: {e}")
            LOGGER.exception(e, context=f"Error analyzing {json_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run all LLM bias tests sequentially.")

    # Test LLM Selection
    test_llm_group = parser.add_mutually_exclusive_group(required=True)
    test_llm_group.add_argument("--test-llm-id", help="ID of the Test LLM (e.g., 'gpt-5.4-mini', 'claude-sonnet-4-6', or custom model ID). Required if --test-llm-name is not used.")
    test_llm_group.add_argument("--test-llm-name", help="Name of the Test LLM as defined in config.json. Required if --test-llm-id is not used.")

    # Judge LLM Selection
    judge_llm_group = parser.add_mutually_exclusive_group(required=True)
    judge_llm_group.add_argument("--judge-llm-id", help="ID of the Judge LLM (e.g., 'gpt-5.4-mini', 'claude-sonnet-4-6', or custom model ID). Required if --judge-llm-name is not used.")
    judge_llm_group.add_argument("--judge-llm-name", help="Name of the Judge LLM as defined in config.json. Required if --judge-llm-id is not used.")

    # --- Other ---
    parser.add_argument('--runs', type=int, default=1, help='Number of times to run the full test suite.')
    parser.add_argument(
        '--num-questions',
        type=int,
        default=None, # Default to None, meaning use all questions
        help='Number of questions to run per test. Passed down to sub-scripts.'
    )
    parser.add_argument(
        '--request-timeout-seconds',
        type=int,
        default=15 * 60,
        help='Per-answer request timeout in seconds. Passed down to sub-scripts.'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        default=None,
        help='Enable verbose debug logging and mirror log output to stdout.'
    )
    parsed_args = parser.parse_args()
    debug_state = is_debug_enabled(parsed_args.debug)
    LOGGER.set_debug(debug_state)
    if debug_state:
        os.environ[DEBUG_ENV_VAR] = "1"
    main(parsed_args)
