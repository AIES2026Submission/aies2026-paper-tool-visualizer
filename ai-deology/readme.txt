AI DEOLOGY - PYTHON WORKFLOW
==============================

AI Deology runs entirely from a Python CLI now, so you can drive the whole
experiment stack over SSH or on a headless box without needing Electron or
any GUI.

PREREQUISITES
--------------
- Python 3.10+ (3.11, 3.12, 3.13 all fine)
- pip
- API keys for whichever providers you're using (OpenAI, Anthropic, Google,
  DeepSeek, etc.)

SETUP
-----
git clone <this repo>
cd <repo-root>

# Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
python -m pip install -r ai-deology/requirements.txt

If you'd rather work from inside the subdirectory afterward:

cd ai-deology
python launcher.py

ENVIRONMENT VARIABLES
----------------------
Create ai-deology/.env (or just export these in your shell) with whatever
providers you're planning to use:

OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
DEEPSEEK_API_KEY=...

Custom API models pull their credentials from whatever environment variable
name you set for them in config.json.

INTERACTIVE CLI LAUNCHER
--------------------------
launcher.py is the main entry point for remote use - it's a simple ANSI menu
that works fine over SSH.

cd <repo-root>
source .venv/bin/activate
python ai-deology/launcher.py

Menu options:

1. Run Tests
   Pick the Test LLM, Judge LLM, choose T1/T2/T3 (or all of them), set
   bias/slant options, and watch the scripts run in place. You can rerun
   any batch or individual test straight from the menu, and the number of
   questions per test is capped from the Settings screen.

2. View Results
   Browse the results/ tree, drill into a model's folder, and get a text
   summary of each JSON file - question counts, rating breakdowns, score
   stats, a few sample questions. Works for raw runs and aggregated output
   alike.

3. Aggregate Results
   Runs scripts/results_aggregator.py and scripts/pc_converter.py to scan
   every result folder and write summaries into
   results/Aggregated Results/...

4. Settings
   Adjust questions-per-test, the per-answer timeout, or manage custom
   models stored in config.json.

5. Exit

Since it all runs in the terminal, there's no display server or desktop
runtime needed - works well on a server you're only reaching over SSH.

RUNNING SCRIPTS DIRECTLY
--------------------------
Each experiment also works as its own standalone CLI if you want to
automate things or wire it into other tooling:

# Test 1
python ai-deology/scripts/llm_test1.py --test1 --test-llm-id gpt-5.4-mini --judge-llm-id gpt-5.4-mini

# Test 2 (bias injection)
python ai-deology/scripts/llm_test2.py --bias-type left --test-llm-name "deepseek-r1" --judge-llm-name "atla/selene-mini"

# Test 3 (slanted questions)
python ai-deology/scripts/llm_test3.py --test3 --question-slant right --test-llm-id claude-haiku-4-5 --judge-llm-id gpt-5.4-mini

# Run everything, back to back
python ai-deology/scripts/llm_test_all.py --test-llm-name "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:latest" --judge-llm-name "atla/selene-mini" --runs 2

Pass --help to any script to see the full argument list. All of them read
from the shared ai-deology/config.json and ai-deology/.env.

TEST 2 BIAS CONTEXT
---------------------
Test 2 seeds each prompt with a prewritten left- or right-leaning
conversation pulled from data/political_compass/*_bias_history.txt. When
the actual Political Compass question gets injected, it's tacked onto the
final user turn with a natural segue ("By the way, I'd love your
perspective on this:") so the Test LLM reads it as a continuation of the
chat rather than an obvious prompt break. The history files on disk stay
untouched - only the live payload sent for each API call gets modified.

CUSTOM MODELS AND CONFIGURATION
----------------------------------
- Add or remove entries in config.json through Settings > Custom Models
  inside launcher.py.
- Each entry stores the model name, type (api or local), identifier or
  endpoint, and (for api types) the environment variable holding its key.
  The scripts pick these up automatically.
- Built-in API examples currently cover gpt-5.4, gpt-5.4-mini,
  gpt-5.4-nano, claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5,
  gemini-2.5-pro, gemini-2.5-flash, and gemini-2.5-flash-lite.
- The per-answer timeout lives in config.json as request_timeout_seconds
  and can be changed from the launcher's Settings menu.

VIEWING AND EXPORTING RESULTS
--------------------------------
- Raw runs land in results/T{1,2,3}/<TestModel>_<JudgeModel>/...json
- Aggregated summaries go under results/Aggregated Results/
- The CLI viewer shows the most recent files, rating distributions, score
  stats, and a handful of representative questions so you can check a run
  without opening a separate editor.
- For anything more involved, use scripts/results_aggregator.py or
  scripts/analyze_results.py directly and process the JSON however you
  need.

TROUBLESHOOTING
-----------------
- Make sure the repo-root .venv is activated before running launcher.py -
  otherwise it can fall back to a system Python missing the required
  packages.
- Over SSH, make sure your terminal handles ANSI escape codes (most do by
  default; export TERM=xterm-256color usually does the trick if not).
- If hosted API models aren't working, double check the matching SDKs from
  requirements.txt actually got installed into the active venv.
- If local model requests fail, confirm requests is installed in the venv,
  then check that the Ollama endpoint is reachable from the machine
  running the CLI.
- GUI/Electron packages are gone - use the CLI workflow above.