LLMs on the Political Compass: Prompt-Conditioned Positioning and Directional Drift
====================================================================================

This repository contains the tools described in the paper "LLMs on the
Political Compass: Prompt-Conditioned Positioning and Directional Drift,"
submitted to AIES 2026. Refer to the paper for a fuller explanation of
their purpose and use.

- T1: baseline answers to the original questions
- T2: the same questions after left- or right-leaning conversational
  injection
- T3: the same evaluation after reframing the questions themselves

The repo is organized as two connected parts:

- ai-deology/   the Python CLI and experiment scripts
- visualizer/   the static dashboard and methodology pages

ai-deology/results/ contains the source files. visualizer/data.js is the
generated bundle read by the browser.

REPOSITORY LAYOUT
--------------------
.
├── ai-deology/
│   ├── launcher.py
│   ├── scripts/
│   ├── results/
│   ├── config.json
│   ├── requirements.txt
│   └── readme.txt
├── visualizer/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── data.js
│   ├── scripts/
│   └── readme.txt
└── artifacts/

Important paths:

- ai-deology/results/                    source of truth for experiment
                                          output
- ai-deology/results/T1, T2, T3          raw run outputs
- ai-deology/results/Aggregated Results/ aggregated Political Compass
                                          summaries
- visualizer/data.js                     generated dataset consumed by
                                          the dashboard
- artifacts/                             local exports and scratch
                                          outputs

QUICK START
-------------
Clone the repo, create a virtual environment at the repo root, install
dependencies, then launch the CLI:

    git clone <repo-url>
    cd <repo-root>

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r ai-deology/requirements.txt

    python ai-deology/launcher.py

On Windows:

    .venv\Scripts\activate

PROVIDER CONFIGURATION
--------------------------
Create ai-deology/.env if you want to use hosted API models:

    OPENAI_API_KEY=...
    ANTHROPIC_API_KEY=...
    GOOGLE_API_KEY=...
    DEEPSEEK_API_KEY=...

You only need the variables for the providers you actually use.

For local models, add them through launcher.py -> Settings -> Custom
Models. Those entries are stored in ai-deology/config.json. If you use
Ollama or another local server, make sure that service is already
running before you start a test run.

TYPICAL WORKFLOW
-------------------

1. Run experiments
   -----------------
   The main entry point is the interactive launcher:

       source .venv/bin/activate
       python ai-deology/launcher.py

   From the launcher you can:

   - choose the Test LLM and Judge LLM
   - run T1, T2, T3, or the full battery
   - limit the number of questions
   - configure the per-answer timeout
   - add or remove custom local/API models
   - inspect saved results
   - aggregate results into Political Compass summaries

   Direct script usage is documented in ai-deology/readme.txt.

2. Aggregate results
   -------------------
   If you run experiments manually and want to rebuild the aggregated
   summaries:

       python ai-deology/scripts/results_aggregator.py
       python ai-deology/scripts/pc_converter.py

   The launcher can do this for you from its "Aggregate Results" menu
   entry.

3. Refresh the dashboard dataset
   --------------------------------
   If you already have results and want to regenerate the visualizer
   bundle:

       python visualizer/scripts/run_pc_scripts_and_sync.py --sync-only

   That command:

   - normalizes a legacy nested ai-deology/results/political_compass/
     layout if it exists
   - rebuilds visualizer/data.js
   - keeps the dashboard aligned with the latest aggregated results

4. Preview the visualizer locally
   -----------------------------------
       cd visualizer
       python3 -m http.server 8000

   Then open http://localhost:8000

HOW THE VISUALIZER GETS ITS DATA
------------------------------------
The default dashboard dataset is not loaded live from the filesystem.
Instead:

1. Experiment scripts write raw JSON into ai-deology/results/T1, T2, and
   T3.
2. Aggregation scripts write Political Compass summaries into
   ai-deology/results/Aggregated Results/.
3. visualizer/scripts/build_data.py reads those aggregated results and
   writes visualizer/data.js.
4. visualizer/index.html loads data.js, and visualizer/app.js reads
   window.experimentData from that bundle.

The visualizer uses a generated snapshot of ai-deology/results/ rather than
reading the raw folders directly in the browser.

If you update the experiment results and do not rebuild
visualizer/data.js, the dashboard will still show the old snapshot.

DOCUMENTATION MAP
--------------------
- ai-deology/readme.txt         Python CLI, direct script usage, config,
                                 and troubleshooting
- visualizer/readme.txt         dashboard structure and rebuild steps
- visualizer/methodology.html   long-form methodology and scoring
                                 explanation
TROUBLESHOOTING
-------------------
- If a provider model fails immediately, first check that the matching
  API key is present in ai-deology/.env or in your shell environment.
- If a local model fails, verify that the local inference server is
  running and reachable from the same machine.
- If the dashboard looks stale, rebuild visualizer/data.js from the
  current results tree.
- If Python imports fail, make sure the repo-root .venv is activated
  before running launcher.py.

Generative AI tools were used to assist with the implementation and debugging of parts of the analysis code.