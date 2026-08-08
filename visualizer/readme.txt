VISUALIZER
============

This directory contains the publishable dashboard and supporting research
material.

- index.html, app.js, styles.css, data.js   the static dashboard bundle
- methodology.html                          the long-form methodology
- scripts/                                  rebuild and analysis helpers
- references/                               source material used to
                                             verify the Political Compass
                                             formula

The dashboard bundle is rebuilt from the results stored under
../ai-deology/results/.

DATA FLOW
-----------
The browser does not read the raw experiment folders directly.

1. ai-deology/results/T1, T2, and T3 store raw run outputs.
2. ai-deology/results/Aggregated Results/ stores aggregated Political
   Compass summaries.
3. scripts/build_data.py reads those aggregated files and writes
   data.js.
4. index.html loads data.js, and app.js renders window.experimentData.

If the results tree changes, you must rebuild data.js or the dashboard
will still show the old snapshot.

REBUILD THE DASHBOARD DATASET
---------------------------------
    python3 scripts/build_data.py

Or, from the repo root:

    python3 visualizer/scripts/run_pc_scripts_and_sync.py --sync-only

That wrapper also handles a legacy nested
ai-deology/results/political_compass/ layout before rebuilding the
bundle.

LOCAL PREVIEW
----------------
    python3 -m http.server 8000

Then open http://localhost:8000
