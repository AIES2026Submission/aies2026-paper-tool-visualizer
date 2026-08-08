function setupDataImport() {
    const importBtn = document.getElementById('importBtn');
    const fileInput = document.getElementById('dataFileInput');
    const datasetLabel = document.getElementById('datasetLabel');

    if (!importBtn || !fileInput) return;

    importBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        try {
            const text = await file.text();
            let data;

            if (file.name.endsWith('.js')) {
                const match = text.match(/window\.experimentData\s*=\s*(\{[\s\S]*\})\s*;?\s*$/);
                if (match) {
                    data = JSON.parse(match[1]);
                } else {
                    throw new Error('Could not find experimentData in .js file');
                }
            } else {
                data = JSON.parse(text);
            }

            if (!validateDataFormat(data)) {
                throw new Error('Invalid data format');
            }

            loadNewData(data, file.name);

            if (datasetLabel) {
                datasetLabel.textContent = file.name;
                datasetLabel.classList.add('loaded');
            }

        } catch (err) {
            console.error('Failed to import data:', err);
            alert(`Failed to import data: ${err.message}\n\nExpected format:\n{\n  "MODEL_PAIR": {\n    "T1|T2-LEFT|T2-RIGHT|T3-LEFT|T3-RIGHT": {\n      "Question text": {\n        "average_score": number,\n        ...\n      }\n    }\n  }\n}`);
        }

        fileInput.value = '';
    });
}

function validateDataFormat(data) {
    if (typeof data !== 'object' || data === null) return false;

    const models = Object.keys(data);
    if (models.length === 0) return false;

    const firstModel = data[models[0]];
    if (typeof firstModel !== 'object') return false;

    const conditions = Object.keys(firstModel);
    if (conditions.length === 0) return false;

    const firstCondition = firstModel[conditions[0]];
    if (typeof firstCondition !== 'object') return false;

    // Format A (new PC data): condition has numeric axis scores and per_question array.
    const isPCFormat = (
        typeof firstCondition.economic_score === 'number' &&
        typeof firstCondition.social_score === 'number' &&
        Array.isArray(firstCondition.per_question)
    );

    // Format B (legacy/raw data): condition is a map of question -> { average_score: number }.
    const questionKeys = Object.keys(firstCondition);
    const firstQuestion = questionKeys.length > 0 ? firstCondition[questionKeys[0]] : null;
    const isLegacyFormat = (
        questionKeys.length > 0 &&
        typeof firstQuestion === 'object' &&
        firstQuestion !== null &&
        typeof firstQuestion.average_score === 'number'
    );

    if (!isPCFormat && !isLegacyFormat) return false;

    return true;
}

function setupExport() {
    const exportBtn = document.getElementById('exportBtn');
    if (!exportBtn) return;

    exportBtn.addEventListener('click', () => {
        if (!window.experimentData) {
            alert('No data to export');
            return;
        }

        const dataStr = JSON.stringify(window.experimentData, null, 2);
        const blob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = 'experiment_data.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });
}

function setupDataReload() {
    const reloadBtn = document.getElementById('reloadDataBtn');
    const datasetLabel = document.getElementById('datasetLabel');
    if (!reloadBtn) return;

    const setLoading = (isLoading) => {
        reloadBtn.disabled = isLoading;
        reloadBtn.style.opacity = isLoading ? '0.7' : '1';
        reloadBtn.style.cursor = isLoading ? 'wait' : '';
    };

    const loadFromScriptTag = (src) => new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.async = true;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('Script load failed'));
        document.head.appendChild(script);
    });

    const parseDataJsText = (text) => {
        const match = text.match(/window\.experimentData\s*=\s*(\{[\s\S]*\})\s*;?\s*$/);
        if (!match) throw new Error('Could not parse experimentData from data.js');
        const parsed = JSON.parse(match[1]);
        if (!validateDataFormat(parsed)) throw new Error('Reloaded data has invalid format');
        return parsed;
    };

    reloadBtn.addEventListener('click', async () => {
        setLoading(true);

        try {
            // In file:// contexts, query params can break local path resolution.
            const isFileProtocol = window.location.protocol === 'file:';
            const url = isFileProtocol ? 'data.js' : `data.js?t=${Date.now()}`;
            const response = await fetch(url, { cache: 'no-store' });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const text = await response.text();
            const data = parseDataJsText(text);

            loadNewData(data, 'data.js (reloaded)');
            if (datasetLabel) datasetLabel.classList.add('loaded');
        } catch (fetchErr) {
            try {
                // Try cache-busted URL first, then plain file path fallback.
                try {
                    await loadFromScriptTag(`data.js?t=${Date.now()}`);
                } catch (_) {
                    await loadFromScriptTag('data.js');
                }

                if (!window.experimentData || !validateDataFormat(window.experimentData)) {
                    throw new Error('window.experimentData is missing or invalid after script reload');
                }

                loadNewData(window.experimentData, 'data.js (reloaded)');
                if (datasetLabel) datasetLabel.classList.add('loaded');
            } catch (scriptErr) {
                console.error('Reload failed (fetch + script):', fetchErr, scriptErr);
                alert(`Failed to reload data.js.\n\nFetch error: ${fetchErr.message}\nScript error: ${scriptErr.message}`);
            }
        } finally {
            setLoading(false);
        }
    });
}

function loadNewData(data, filename) {
    window.experimentData = data;

    state.models = processData(data);

    assignModelVisuals();

    state.selectedModel = 'all';

    const select = document.getElementById('modelFilter');
    if (select) {
        select.innerHTML = '<option value="all">Compare All Models</option>';
        Object.keys(state.models).forEach(m => {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = m;
            select.appendChild(opt);
        });
    }

    const metaInfo = document.querySelector('.meta-info');
    if (metaInfo) {
        const modelCount = Object.keys(state.models).length;
        metaInfo.innerHTML = `
            <span>N=${modelCount} Models</span> • 
            <span>Conditions: Baseline (T1), Injection (T2), Framing (T3)</span> • 
            <span>Dataset: ${filename}</span>
        `;
    }

    if (state.view === 'multiples') {
        renderSmallMultiples();
    } else {
        const filter = getVectorFilterForView(state.view);
        drawCompass(null, 'all', filter);
    }

    updateModelList();
    updateDriftStats();
    updateIdeologyPanel();
    updateCharts();

    console.log(`Loaded ${filename} with ${Object.keys(state.models).length} models`);
}

// Political Compass Coordinate System:
// X-axis (Economic): Left (-10) to Right (+10)
// Y-axis (Social): Libertarian (-10) to Authoritarian (+10)
// 
// Using official Political Compass formula from politicalcompass.github.io:
// - 62 questions, each weighted for Economic and/or Social axes
// - Scores normalized: economic = sumE/8.0 + 0.38, social = sumS/19.5 + 2.41

const CONFIG = {
    colors: {
        left: '#ff3b30',   // Red
        right: '#007aff',  // Blue
        lib: '#34c759',    // Green
        auth: '#5856d6',   // Purple

        palette: [
            '#ff3b30', // Red
            '#ff9500', // Orange
            '#ffcc00', // Yellow
            '#34c759', // Green
            '#00c7be', // Teal
            '#32ade6', // Light Blue
            '#007aff', // Blue
            '#5856d6', // Purple
            '#af52de', // Indigo
            '#ff2d55', // Pink
            '#a2845e', // Brown
            '#8e8e93', // Gray
        ],
        modelMap: {
            'Claude': '#ff3b30',      // Red
            'Gemma': '#34c759',       // Green
            'Qwen': '#007aff',        // Blue
            'DeepSeek': '#5856d6',    // Purple
            'GPT': '#ff9500',         // Orange
            'Llama': '#000075',       // Navy
            'Mistral': '#00c7be',     // Teal
            'Magistral': '#ff2d55',   // Pink
            'Phi': '#ffcc00',         // Yellow
            'Hermes': '#af52de',      // Indigo
            'Granite': '#8e8e93',     // Gray
            'OLMo': '#a2845e'         // Brown
        }
    }
};


const REGION_CENTER_DEADZONE = 1.0;
const REGION_SLIGHT_THRESHOLD = 2.2;
const REGION_MODERATE_THRESHOLD = 4.5;

function getQuadrantLabel(x, y) {
    const horizontal = x >= 0 ? 'Right' : 'Left';
    const vertical = y >= 0 ? 'Authoritarian' : 'Libertarian';
    return `${horizontal}-${vertical}`;
}

function getQuadrantTierPrefix(xAbs, yAbs) {
    const intensity = Math.max(xAbs, yAbs);
    if (intensity < REGION_SLIGHT_THRESHOLD) return 'Slightly';
    if (intensity < REGION_MODERATE_THRESHOLD) return 'Moderately';
    return 'Strongly';
}

function getRegionAxisSummary(regionId) {
    if (regionId === 'LL') return 'left of the Y-axis and below the X-axis';
    if (regionId === 'LR') return 'right of the Y-axis and below the X-axis';
    if (regionId === 'AL') return 'left of the Y-axis and above the X-axis';
    if (regionId === 'AR') return 'right of the Y-axis and above the X-axis';
    return `within the conservative center band (economic and social scores both between -${REGION_CENTER_DEADZONE} and +${REGION_CENTER_DEADZONE})`;
}

function getIdeologyInterpretation(x, y) {
    const xAbs = Math.abs(x);
    const yAbs = Math.abs(y);

    if (xAbs < REGION_CENTER_DEADZONE && yAbs < REGION_CENTER_DEADZONE) {
        return {
            label: 'Center',
            desc: `Position at (${x.toFixed(1)}, ${y.toFixed(1)}): near the center.`
        };
    }

    const baseQuadrant = getQuadrantLabel(x, y);
    const tierPrefix = getQuadrantTierPrefix(xAbs, yAbs);
    const label = `${tierPrefix} ${baseQuadrant}`;
    const desc = `Position at (${x.toFixed(1)}, ${y.toFixed(1)}): ${label}.`;

    return { label, desc };
}

function getRegionLabel(x, y, deadzone = REGION_CENTER_DEADZONE) {
    const xAbs = Math.abs(x);
    const yAbs = Math.abs(y);

    if (xAbs < deadzone && yAbs < deadzone) return 'Center';

    const baseQuadrant = getQuadrantLabel(x, y);
    const tierPrefix = getQuadrantTierPrefix(xAbs, yAbs);
    return `${tierPrefix} ${baseQuadrant}`;
}

function getRegionId(x, y, deadzone = REGION_CENTER_DEADZONE) {
    const xCentrist = Math.abs(x) < deadzone;
    const yCentrist = Math.abs(y) < deadzone;

    if (xCentrist && yCentrist) return 'C';
    if (x < 0 && y < 0) return 'LL';
    if (x >= 0 && y < 0) return 'LR';
    if (x < 0 && y >= 0) return 'AL';
    return 'AR';
}

const REGION_LABELS = {
    'LL': 'Left-Libertarian',
    'LR': 'Right-Libertarian',
    'AL': 'Left-Authoritarian',
    'AR': 'Right-Authoritarian',
    'C': 'Center'
};

const QUADRANT_LABELS = REGION_LABELS;
const getQuadrantId = getRegionId;


const state = {
    view: 'main', // 'main' | 't2' | 't3' | 'multiples'
    showArrows: true,
    selectedModel: 'all',
    models: {}, // Processed data
    modelColors: {}, // Dynamic color mapping
    modelShapes: {}, // Dynamic shape mapping
    charts: {}, // Chart instances
    transform: { k: 1, x: 0, y: 0 }, // Zoom/Pan transform
    isDragging: false,
    lastMouse: { x: 0, y: 0 },
    hitRegions: [] // Stores clickable regions on the compass {x, y, r, model, type}
};


const MODEL_DISPLAY_NAMES = {
    'GEMMA': 'Gemma 3 (27B)',
    'QWEN3': 'Qwen 3 (14.8B)',
    'DEEPSEEK': 'DeepSeek-R1 (14.8B)',
    'LLAMA3': 'Llama 3.1 (8B)',
    'MISTRAL': 'Mistral (7B)',
    'MAGISTRAL': 'Magistral (23.6B)',
    'PHI4': 'Phi-4 Reasoning (14.7B)',
    'GPT_OSS': 'GPT-OSS (20.9B)',
    'HERMES': 'Hermes 4 (14.8B)',
    'GRANITE': 'Granite 4.0 Tiny',
    'OLMO': 'OLMo (3.7B)',
    'CLAUDE': 'Claude'
};

function processData(rawData) {
    const processed = {};

    for (const [folder, conditions] of Object.entries(rawData)) {
        let key = folder.split('_')[0];
        if (folder.includes('GEMMA')) key = 'GEMMA';
        if (folder.includes('QWEN')) key = 'QWEN3';
        if (folder.includes('DEEPSEEK')) key = 'DEEPSEEK';
        if (folder.includes('LLAMA')) key = 'LLAMA3';
        if (folder.includes('MISTRAL')) key = 'MISTRAL';
        if (folder.includes('MAGISTRAL')) key = 'MAGISTRAL';
        if (folder.includes('PHI4')) key = 'PHI4';
        if (folder.includes('GPT_OSS')) key = 'GPT_OSS';
        if (folder.includes('HERMES')) key = 'HERMES';
        if (folder.includes('GRANITE')) key = 'GRANITE';
        if (folder.includes('OLMO')) key = 'OLMO';
        if (folder.startsWith('CLAUDE')) key = 'CLAUDE';

        const name = MODEL_DISPLAY_NAMES[key] || key;

        if (!processed[name]) processed[name] = {};

        for (const [cond, pcData] of Object.entries(conditions)) {
            processed[name][cond] = extractPCCoordinates(pcData);
        }
    }
    return processed;
}

function extractPCCoordinates(pcData) {
    // Political Compass format has pre-calculated scores
    // economic_score: X-axis, Left (-) to Right (+)
    // social_score: Y-axis, Libertarian (-) to Authoritarian (+)

    const x = pcData.economic_score || 0;
    const y = pcData.social_score || 0;
    const questionCount = pcData.question_count || 62;
    const missingQuestions = pcData.missing_questions || [];

    // Use root-level totals from _pc.json (more accurate than recalculating)
    const totalCommitted = pcData.total_committed || 0;
    const totalNeutral = pcData.total_neutral || 0;
    const totalRefusals = pcData.total_refusals || 0;
    const totalItems = pcData.total_items || (questionCount * 10);

    // Calculate total answered runs (committed + neutral, excludes refusals)
    const totalAnswered = totalCommitted + totalNeutral;

    // Calculate engagement and commitment rates (RUN-LEVEL metrics)
    // Engagement: % of runs that resulted in an answer (not refused)
    const engagement = totalItems > 0 ? Math.round((totalAnswered / totalItems) * 1000) / 10 : 0;

    // Commitment: % of answered runs that took a position (not neutral)
    const commitment = totalAnswered > 0 ? Math.round((totalCommitted / totalAnswered) * 100) : 0;

    // Refusal rate
    const refusalRate = totalItems > 0 ? Math.round((totalRefusals / totalItems) * 1000) / 10 : 0;

    return {
        x: x,  // Economic: Left (-10) to Right (+10)
        y: y,  // Social: Libertarian (-10) to Authoritarian (+10)

        // Raw PC sums (for reference)
        econSum: pcData.econ_sum || 0,
        socSum: pcData.soc_sum || 0,

        // Metrics (using root-level totals from _pc.json)
        engagement: engagement,
        econEngagement: engagement,
        socialEngagement: engagement,

        commitment: commitment,
        econCommitment: commitment,
        socialCommitment: commitment,

        refusalRate: refusalRate,
        totalRefusals: totalRefusals,

        // Raw counts
        questionCount: questionCount,
        missingQuestions: missingQuestions.length,
        totalAnswered: totalAnswered,
        totalCommitted: totalCommitted,
        totalNeutral: totalNeutral,
        totalItems: totalItems,

        // Legacy compatibility
        econCommitted: totalCommitted,
        econEngaged: totalAnswered,
        econTotal: totalItems,
        socialCommitted: totalCommitted,
        socialEngaged: totalAnswered,
        socialTotal: totalItems,

        // Per-question breakdown
        perQuestion: pcData.per_question || []
    };
}


// COORDINATE SYSTEM NOTE:
// - Data coordinates: X positive = Economic Right, Y positive = Authoritarian
// - Canvas coordinates: Y increases downward (0,0 at top-left)
// - Therefore we NEGATE Y when converting data → canvas to place Authoritarian at TOP

function getModelShape(name) {
    if (state.modelShapes && state.modelShapes[name]) {
        return state.modelShapes[name];
    }
    return 'circle';
}

function drawShape(ctx, x, y, shape, r, color, opacity) {
    ctx.beginPath();
    ctx.fillStyle = color;
    ctx.strokeStyle = '#000000'; // Stark black stroke
    ctx.lineWidth = 2; // Thicker lines
    ctx.globalAlpha = opacity;

    switch (shape) {
        case 'square':
            ctx.rect(x - r, y - r, r * 2, r * 2);
            break;
        case 'triangle':
            ctx.moveTo(x, y - r);
            ctx.lineTo(x + r, y + r);
            ctx.lineTo(x - r, y + r);
            ctx.closePath();
            break;
        case 'triangle-down':
            ctx.moveTo(x, y + r);
            ctx.lineTo(x + r, y - r);
            ctx.lineTo(x - r, y - r);
            ctx.closePath();
            break;
        case 'diamond':
            ctx.moveTo(x, y - r * 1.3);
            ctx.lineTo(x + r * 1.3, y);
            ctx.lineTo(x, y + r * 1.3);
            ctx.lineTo(x - r * 1.3, y);
            ctx.closePath();
            break;
        case 'star': // 5-point star
            const spikes = 5;
            const outer = r * 1.3;
            const inner = r * 0.5;
            let rot = Math.PI / 2 * 3;
            let xS = x;
            let yS = y;
            const step = Math.PI / spikes;
            ctx.moveTo(x, y - outer);
            for (let i = 0; i < spikes; i++) {
                xS = x + Math.cos(rot) * outer;
                yS = y + Math.sin(rot) * outer;
                ctx.lineTo(xS, yS);
                rot += step;
                xS = x + Math.cos(rot) * inner;
                yS = y + Math.sin(rot) * inner;
                ctx.lineTo(xS, yS);
                rot += step;
            }
            ctx.lineTo(x, y - outer);
            ctx.closePath();
            break;
        case 'hexagon':
            const sides = 6;
            ctx.moveTo(x + r * Math.cos(0), y + r * Math.sin(0));
            for (let i = 1; i <= sides; i += 1) {
                ctx.lineTo(x + r * Math.cos(i * 2 * Math.PI / sides), y + r * Math.sin(i * 2 * Math.PI / sides));
            }
            ctx.closePath();
            break;
        case 'cross':
            const w = r * 0.4; // width of arm
            const l = r * 1.2; // length of arm
            ctx.moveTo(x - w, y - l);
            ctx.lineTo(x + w, y - l);
            ctx.lineTo(x + w, y - w);
            ctx.lineTo(x + l, y - w);
            ctx.lineTo(x + l, y + w);
            ctx.lineTo(x + w, y + w);
            ctx.lineTo(x + w, y + l);
            ctx.lineTo(x - w, y + l);
            ctx.lineTo(x - w, y + w);
            ctx.lineTo(x - l, y + w);
            ctx.lineTo(x - l, y - w);
            ctx.lineTo(x - w, y - w);
            ctx.closePath();
            break;
        case 'pentagon':
            const pSides = 5;
            const offset = -Math.PI / 2;
            ctx.moveTo(x + r * Math.cos(offset), y + r * Math.sin(offset));
            for (let i = 1; i <= pSides; i++) {
                ctx.lineTo(x + r * Math.cos(offset + i * 2 * Math.PI / pSides), y + r * Math.sin(offset + i * 2 * Math.PI / pSides));
            }
            ctx.closePath();
            break;
        case 'circle':
        default:
            ctx.arc(x, y, r, 0, Math.PI * 2);
            break;
    }

    ctx.fill();
    ctx.globalAlpha = 1;
    ctx.stroke();
}

function getShapeSVG(shape, color, size = 16) {
    const cx = size / 2;
    const cy = size / 2;
    const r = size * 0.35; // Base radius

    // Helper to generate polygon points
    const poly = (points) => `<polygon points="${points}" fill="${color}" stroke="black" stroke-width="1.5"/>`;

    switch (shape) {
        case 'circle':
            return `<svg width="${size}" height="${size}" style="flex-shrink:0; margin-right:8px;"><circle cx="${cx}" cy="${cy}" r="${r}" fill="${color}" stroke="black" stroke-width="1.5"/></svg>`;

        case 'square':
            return `<svg width="${size}" height="${size}" style="flex-shrink:0; margin-right:8px;"><rect x="${cx - r}" y="${cy - r}" width="${r * 2}" height="${r * 2}" fill="${color}" stroke="black" stroke-width="1.5"/></svg>`;

        case 'triangle':
            return `<svg width="${size}" height="${size}" style="flex-shrink:0; margin-right:8px;">${poly(`${cx},${cy - r} ${cx + r},${cy + r} ${cx - r},${cy + r}`)}</svg>`;

        case 'triangle-down':
            return `<svg width="${size}" height="${size}" style="flex-shrink:0; margin-right:8px;">${poly(`${cx},${cy + r} ${cx + r},${cy - r} ${cx - r},${cy - r}`)}</svg>`;

        case 'diamond':
            const rd = r * 1.3;
            return `<svg width="${size}" height="${size}" style="flex-shrink:0; margin-right:8px;">${poly(`${cx},${cy - rd} ${cx + rd},${cy} ${cx},${cy + rd} ${cx - rd},${cy}`)}</svg>`;

        case 'star':
            const outer = r * 1.3;
            const inner = r * 0.5;
            const ps = [];
            for (let i = 0; i < 10; i++) {
                const angle = Math.PI / 2 * 3 + i * Math.PI / 5;
                const rad = i % 2 === 0 ? outer : inner;
                ps.push(`${cx + Math.cos(angle) * rad},${cy + Math.sin(angle) * rad}`);
            }
            return `<svg width="${size}" height="${size}" style="flex-shrink:0; margin-right:8px;">${poly(ps.join(' '))}</svg>`;

        case 'hexagon':
            const ph = [];
            for (let i = 0; i < 6; i++) {
                const angle = i * Math.PI / 3;
                ph.push(`${cx + Math.cos(angle) * r},${cy + Math.sin(angle) * r}`);
            }
            return `<svg width="${size}" height="${size}" style="flex-shrink:0; margin-right:8px;">${poly(ph.join(' '))}</svg>`;

        case 'cross':
            const w = r * 0.4;
            const l = r * 1.2;
            const pc = [
                [cx - w, cy - l], [cx + w, cy - l], [cx + w, cy - w], [cx + l, cy - w],
                [cx + l, cy + w], [cx + w, cy + w], [cx + w, cy + l], [cx - w, cy + l],
                [cx - w, cy + w], [cx - l, cy + w], [cx - l, cy - w], [cx - w, cy - w]
            ].map(p => p.join(',')).join(' ');
            return `<svg width="${size}" height="${size}" style="flex-shrink:0; margin-right:8px;">${poly(pc)}</svg>`;

        case 'pentagon':
            const pp = [];
            for (let i = 0; i < 5; i++) {
                const angle = -Math.PI / 2 + i * 2 * Math.PI / 5;
                pp.push(`${cx + Math.cos(angle) * r},${cy + Math.sin(angle) * r}`);
            }
            return `<svg width="${size}" height="${size}" style="flex-shrink:0; margin-right:8px;">${poly(pp.join(' '))}</svg>`;

        default:
            return `<svg width="${size}" height="${size}" style="flex-shrink:0; margin-right:8px;"><circle cx="${cx}" cy="${cy}" r="${r}" fill="${color}" stroke="black" stroke-width="1.5"/></svg>`;
    }
}

function assignModelVisuals() {
    const models = Object.keys(state.models).sort(); // Sort alphabetically for consistency
    const availableShapes = ['circle', 'cross', 'diamond', 'square', 'triangle', 'star', 'hexagon', 'pentagon', 'triangle-down'];

    models.forEach((m, i) => {
        // Colors
        if (!state.modelColors) state.modelColors = {};
        if (!state.modelColors[m]) {
            // Check for partial match in manual map
            let assigned = null;
            for (const [key, col] of Object.entries(CONFIG.colors.modelMap)) {
                if (m.toUpperCase().includes(key)) {
                    assigned = col;
                    break;
                }
            }
            // Fallback to palette
            if (!assigned) {
                assigned = CONFIG.colors.palette[i % CONFIG.colors.palette.length];
            }
            state.modelColors[m] = assigned;
        }

        // Shapes (Assign sequentially based on sorted order)
        if (!state.modelShapes) state.modelShapes = {};
        if (!state.modelShapes[m]) {
            state.modelShapes[m] = availableShapes[i % availableShapes.length];
        }
    });
}

// vectorFilter: null (none), 'all', or array of condition strings e.g. ['T2-LEFT', 'T2-RIGHT']
function drawCompass(canvasElement, targetModelName = 'all', vectorFilter = null) {
    const canvas = canvasElement || document.getElementById('compassCanvas');
    if (!canvas) return; // Guard against missing element

    const ctx = canvas.getContext('2d');

    // High DPI handling
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();

    if (canvas.width !== rect.width * dpr || canvas.height !== rect.height * dpr) {
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
    }

    // Reset transform before scaling
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;

    // Apply Zoom/Pan only if this is the main canvas
    if (canvasElement === null || canvasElement.id === 'compassCanvas') {
        ctx.translate(state.transform.x, state.transform.y);
        ctx.scale(state.transform.k, state.transform.k);
    }

    const cx = w / 2;
    const cy = h / 2;
    const scale = Math.min(w, h) / 20; // Scale factor - matches original Political Compass (±10 reaches edges)

    // Clear hit regions if this is the main canvas
    if (!targetModelName || targetModelName === 'all') {
        state.hitRegions = [];
    }

    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Solid background for canvas
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.restore();

    // Grid
    ctx.beginPath();
    ctx.strokeStyle = 'rgba(0,0,0,0.1)'; // Sharp but subtle black grid
    ctx.lineWidth = 1 / (state.transform.k || 1);

    // Minor grid lines (every 1 unit) - matches original Political Compass
    for (let i = -10; i <= 10; i++) {
        if (i === 0) continue;
        const pos = i * scale;

        ctx.moveTo(cx + pos, 0);
        ctx.lineTo(cx + pos, h);

        ctx.moveTo(0, cy + pos);
        ctx.lineTo(w, cy + pos);
    }
    ctx.stroke();

    ctx.beginPath();
    ctx.strokeStyle = '#000000'; // Pure black axes
    ctx.lineWidth = 2 / (state.transform.k || 1); // Thicker axes

    ctx.moveTo(0, cy);
    ctx.lineTo(w, cy);

    ctx.moveTo(cx, 0);
    ctx.lineTo(cx, h);
    ctx.stroke();


    const modelsToDraw = targetModelName === 'all' ? Object.keys(state.models) : [targetModelName];

    modelsToDraw.forEach(modelName => {
        const model = state.models[modelName];
        if (!model || !model.T1) return;

        const color = state.modelColors[modelName] || '#333';
        const shape = getModelShape(modelName);

        // In main view: filter others completely if one is selected. In small multiples: always opaque
        const isFiltered = state.selectedModel !== 'all' && targetModelName === 'all';
        // If we are filtering, and this model is not the selected one, skip it entirely
        if (isFiltered && state.selectedModel !== modelName) return;

        const opacity = 1;

        // Draw drift vectors if requested
        if (vectorFilter) {
            const conditions = (vectorFilter === 'all')
                ? ['T2-LEFT', 'T2-RIGHT', 'T3-LEFT', 'T3-RIGHT']
                : vectorFilter;

            // Check if this is a "Single View" (e.g. T2-LEFT only)
            // If vectorFilter has only 1 item, treat it as a landing point view (unless it's part of "all")
            const isSingleView = conditions.length === 1 && vectorFilter !== 'all';

            conditions.forEach(cond => {
                if (model[cond]) {
                    // In combined views (Drift T2/T3), show arrows if toggled
                    if (!isSingleView && state.showArrows) {
                        drawVector(ctx, cx, cy, scale, model.T1, model[cond], cond, opacity);
                    }

                    const lx = cx + model[cond].x * scale;
                    const ly = cy - model[cond].y * scale;

                    // Slightly larger point for single view focus
                    // Scale radius inversely with zoom to keep points from getting huge
                    const baseRadius = isSingleView ? 7 : 5;
                    const radius = baseRadius / Math.sqrt(state.transform.k || 1);

                    drawShape(ctx, lx, ly, shape, radius, color, opacity);

                    // Register hit region (only for main canvas interactions)
                    if (canvasElement === null || canvasElement.id === 'compassCanvas') {
                        // Hit regions need to be in SCREEN coordinates (pre-transform)
                        // So we apply the transform here
                        const tx = (lx * state.transform.k) + state.transform.x;
                        const ty = (ly * state.transform.k) + state.transform.y;

                        state.hitRegions.push({
                            x: tx / dpr,
                            y: ty / dpr,
                            r: (radius * state.transform.k) + 4, // Hit area scales with zoom
                            model: modelName,
                            condition: cond,
                            data: model[cond]
                        });
                    }

                    if (isSingleView) {
                        // Show label for single view points - ONLY if selected or not all
                        if (opacity > 0.5 && (state.selectedModel === modelName || state.selectedModel !== 'all')) {
                            ctx.fillStyle = '#1a1a1a';
                            ctx.font = `500 ${11 / (state.transform.k || 1)}px Inter`;
                            ctx.textAlign = 'center';
                            ctx.fillText(modelName, lx, ly - (12 / (state.transform.k || 1)));
                        }
                    }
                }
            });
        }

        if (!vectorFilter || (vectorFilter && vectorFilter.length > 1) || vectorFilter === 'all') {
            // Note: Y is negated to flip canvas coords (Y+ down) to compass coords (Y+ up = Auth)
            const bx = cx + model.T1.x * scale;
            const by = cy - model.T1.y * scale;

            const baseRadius = 6;
            const radius = baseRadius / Math.sqrt(state.transform.k || 1);

            drawShape(ctx, bx, by, shape, radius, color, opacity);

            // Register hit region for T1
            if (canvasElement === null || canvasElement.id === 'compassCanvas') {
                const tx = (bx * state.transform.k) + state.transform.x;
                const ty = (by * state.transform.k) + state.transform.y;

                state.hitRegions.push({
                    x: tx / dpr,
                    y: ty / dpr,
                    r: (radius * state.transform.k) + 4,
                    model: modelName,
                    condition: 'T1',
                    data: model.T1
                });
            }

            // Label logic: Only show if this specific model is selected
            if (state.selectedModel === modelName) {
                ctx.fillStyle = '#1a1a1a';
                ctx.font = `500 ${11 / (state.transform.k || 1)}px Inter`;
                ctx.textAlign = 'center';
                ctx.fillText(modelName, bx, by - (12 / (state.transform.k || 1)));
            }
        }
    });
}

function drawVector(ctx, cx, cy, scale, start, end, type, opacity) {
    // Note: Y is negated to flip canvas coords (Y+ down) to compass coords (Y+ up = Auth)
    const x1 = cx + start.x * scale;
    const y1 = cy - start.y * scale;
    const x2 = cx + end.x * scale;
    const y2 = cy - end.y * scale;

    let color = '#999';
    if (type.includes('LEFT')) color = CONFIG.colors.left;
    if (type.includes('RIGHT')) color = CONFIG.colors.right;

    const lineWidth = 3;
    const headLen = 10;

    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = lineWidth + 2;
    ctx.lineCap = 'square'; // Sharp ends
    ctx.globalAlpha = opacity;
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'square';
    ctx.globalAlpha = opacity;
    ctx.stroke();
    ctx.globalAlpha = 1;

    const angle = Math.atan2(y2 - y1, x2 - x1);

    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - headLen * Math.cos(angle - Math.PI / 6), y2 - headLen * Math.sin(angle - Math.PI / 6));
    ctx.lineTo(x2 - headLen * Math.cos(angle + Math.PI / 6), y2 - headLen * Math.sin(angle + Math.PI / 6));
    ctx.fillStyle = color;
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 2;
    ctx.globalAlpha = opacity;
    ctx.fill();
    ctx.stroke(); // Stroke over fill for sharp look
    ctx.globalAlpha = 1;
}


function renderSmallMultiples() {
    const container = document.getElementById('multiplesView');
    container.innerHTML = ''; // Clear existing

    Object.keys(state.models).forEach(modelName => {
        const card = document.createElement('div');
        card.className = 'mini-compass-card';

        const title = document.createElement('div');
        title.className = 'mini-compass-title';
        title.textContent = modelName;
        card.appendChild(title);

        const wrapper = document.createElement('div');
        wrapper.className = 'compass-wrapper';
        wrapper.style.display = 'block'; // Override grid for simple view

        const canvas = document.createElement('canvas');
        canvas.className = 'mini-canvas';
        wrapper.appendChild(canvas);
        card.appendChild(wrapper);

        container.appendChild(card);

        requestAnimationFrame(() => {
            drawCompass(canvas, modelName, 'all'); // Always show ALL vectors in small multiples
        });
    });
}


function updateModelList() {
    const container = document.getElementById('modelList');
    container.innerHTML = '';

    Object.keys(state.models).forEach(name => {
        const data = state.models[name];
        const color = state.modelColors[name] || '#333';
        const shape = getModelShape(name);

        const div = document.createElement('div');
        div.className = `model-item ${state.selectedModel === name ? 'selected' : ''}`;
        div.onclick = () => setModel(name === state.selectedModel ? 'all' : name);

        const t1 = data.T1 || { x: 0, y: 0, commitment: 0, engagement: 100, refusalRate: 0 };
        const commitment = t1.commitment || 0;
        const engagement = t1.engagement || 100;
        const refusalRate = t1.refusalRate || 0;

        let commitmentClass = 'high';
        if (commitment < 50) commitmentClass = 'low';
        else if (commitment < 75) commitmentClass = 'medium';

        const refusalIndicator = refusalRate > 0
            ? `<span class="refusal-indicator" title="${refusalRate}% of runs refused">⊘${refusalRate}%</span>`
            : '';

        div.innerHTML = `
            ${getShapeSVG(shape, color)}
            <div class="model-info">
                <div class="model-name">${name}</div>
                <div class="model-coords">
                    Econ: ${t1.x >= 0 ? '+' : ''}${t1.x.toFixed(1)} | Social: ${t1.y >= 0 ? '+' : ''}${t1.y.toFixed(1)}
                    ${refusalIndicator}
                </div>
            </div>
            <div class="commitment-badge ${commitmentClass}" title="Commitment: ${commitment}% non-neutral | Engagement: ${engagement}%">
                ${commitment}%
            </div>
        `;
        container.appendChild(div);
    });
}

function updateDriftStats() {
    const driftContainer = document.getElementById('driftStats');
    const chartContainer = document.getElementById('comparisonCharts');

    if (state.selectedModel === 'all') {
        driftContainer.style.display = 'none';
        chartContainer.style.display = 'block';
        return;
    }

    driftContainer.style.display = 'block';
    chartContainer.style.display = 'block';

    const model = state.models[state.selectedModel];
    if (!model || !model.T1) return;

    // Define conditions with expected drift directions
    // LEFT manipulations: expect economic left (dx < 0) and libertarian (dy < 0)
    // RIGHT manipulations: expect economic right (dx > 0) and authoritarian (dy > 0)
    const conditions = [
        { id: 'T2-LEFT', label: 'Injection (Left)', expectedDx: -1, expectedDy: -1 },
        { id: 'T2-RIGHT', label: 'Injection (Right)', expectedDx: 1, expectedDy: 1 },
        { id: 'T3-LEFT', label: 'Framing (Left)', expectedDx: -1, expectedDy: -1 },
        { id: 'T3-RIGHT', label: 'Framing (Right)', expectedDx: 1, expectedDy: 1 }
    ];

    const getCol = (id) => id.includes('LEFT') ? CONFIG.colors.left : CONFIG.colors.right;

    // Calculate ideological profile with consistency analysis
    let allPositions = [{ x: model.T1.x, y: model.T1.y, label: 'Baseline' }];
    let strengths = [];
    let vulnerabilities = [];
    const baselineRegionLabel = getRegionLabel(model.T1.x, model.T1.y);

    conditions.forEach(cond => {
        if (!model[cond.id]) return;

        allPositions.push({ x: model[cond.id].x, y: model[cond.id].y, label: cond.label });

        const dx = model[cond.id].x - model.T1.x;
        const dy = model[cond.id].y - model.T1.y;
        const threshold = 0.1;
        const econExpected = Math.abs(dx) < threshold ? null : (Math.sign(dx) === cond.expectedDx);
        const socialExpected = Math.abs(dy) < threshold ? null : (Math.sign(dy) === cond.expectedDy);

        if (econExpected === true && socialExpected === true) {
            vulnerabilities.push(cond.label);
        } else if (econExpected === false && socialExpected === false || econExpected === null && socialExpected === null) {
            strengths.push(cond.label);
        }
    });

    const avgX = allPositions.reduce((s, p) => s + p.x, 0) / allPositions.length;
    const avgY = allPositions.reduce((s, p) => s + p.y, 0) / allPositions.length;
    const variance = allPositions.reduce((s, p) => s + Math.sqrt((p.x - avgX) ** 2 + (p.y - avgY) ** 2), 0) / allPositions.length;

    const interp = getIdeologyInterpretation(model.T1.x, model.T1.y);

    // Normalize variance to 0-100 for a simple malleability bar (cap at 3.0)
    const varianceScore = Math.min(variance / 3, 1) * 100;

    driftContainer.innerHTML = `
        <div class="panel" style="padding: 1rem; border: 2px solid var(--border-strong); box-shadow: var(--shadow-md);">
            <div class="panel-header" style="display:flex; justify-content: space-between; align-items:center; gap:0.5rem; border-bottom: 2px solid var(--border-strong); padding-bottom: 0.5rem; margin-bottom: 0.75rem;">
                <div style="display:flex; flex-direction:column;">
                    <span class="panel-title" style="font-size: 1rem; font-weight: 700; text-transform: uppercase;">Ideological Profile</span>
                    <span style="font-size: 0.82rem; color: var(--text-main);">Position metrics under ${conditions.length} pressure tests</span>
                </div>
            </div>

            <div class="panel-body" style="margin-top: 0.75rem; display: grid; gap: 0.75rem;">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div style="font-weight:700; text-transform: uppercase; font-size: 0.8rem;">Baseline</div>
                        <div style="color: var(--text-main); font-size: 0.9rem; font-family: 'JetBrains Mono', monospace;">${baselineRegionLabel}</div>
                    </div>
                    <div style="color: var(--text-muted); font-size: 0.9rem; margin-top: 0.25rem;">
                        ${interp.label} (Econ ${model.T1.x >= 0 ? '+' : ''}${model.T1.x.toFixed(1)}, Social ${model.T1.y >= 0 ? '+' : ''}${model.T1.y.toFixed(1)})
                    </div>
                </div>

                <div class="stat-block" style="display:grid; gap:0.4rem; padding:0.75rem; background: var(--bg-surface); border-radius: 0; border:2px solid var(--border-strong);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:700; text-transform: uppercase; font-size: 0.8rem;">Malleability spectrum</span>
                        <span style="font-size:0.85rem; color: var(--text-main); font-family: 'JetBrains Mono', monospace;">${variance.toFixed(2)} spread</span>
                    </div>
                    <div class="bar-bg" style="height: 12px; background: var(--bg-subtle); border-radius: 0; border: 1px solid var(--border-strong);">
                        <div class="bar-fill" style="width:${varianceScore}%; background:${variance < 1 ? '#34c759' : variance < 2 ? '#ff9500' : '#ff3b30'}; height:100%; border-radius:0;"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.75rem; color: var(--text-light); text-transform: uppercase; font-weight: 600;">
                        <span>Stable</span><span>Highly Malleable</span>
                    </div>
                </div>

                ${(strengths.length + vulnerabilities.length) > 0 ? `
                <div style="display:grid; gap:0.35rem; padding:0.75rem; background: var(--bg-surface); border-radius: 0; border:2px solid var(--border-strong);">
                    <div style="font-weight:700; text-transform: uppercase; font-size: 0.8rem;">How it responds to pressure</div>
                    ${strengths.length > 0 ? `<div style="font-size:0.9rem;"><span style="color:#34c759; font-weight:600;">✓ Holds line against:</span> ${strengths.join(', ')}</div>` : ''}
                    ${vulnerabilities.length > 0 ? `<div style="font-size:0.9rem;"><span style="color:#ff3b30; font-weight:600;">✗ Shifts when facing:</span> ${vulnerabilities.join(', ')}</div>` : ''}
                </div>` : ''}
            </div>
        </div>
    `;

    let cardsHtml = '<div class="drift-matrix">';

    conditions.forEach(cond => {
        if (!model[cond.id]) return;

        const dx = model[cond.id].x - model.T1.x;
        const dy = model[cond.id].y - model.T1.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const width = Math.min(100, (dist / 6) * 100);

        const baselineCommitment = model.T1.commitment || 0;
        const manipCommitment = model[cond.id].commitment || 0;
        const commitmentDelta = manipCommitment - baselineCommitment;

        const baselineRefusal = model.T1.refusalRate || 0;
        const manipRefusal = model[cond.id].refusalRate || 0;
        const refusalDelta = manipRefusal - baselineRefusal;

        // Determine if drift matches expected direction (with small threshold for "no movement")
        const threshold = 0.1;
        const econExpected = Math.abs(dx) < threshold ? null : (Math.sign(dx) === cond.expectedDx);
        const socialExpected = Math.abs(dy) < threshold ? null : (Math.sign(dy) === cond.expectedDy);

        let complianceClass, complianceLabel, complianceDesc;
        if (econExpected === true && socialExpected === true) {
            complianceClass = 'compliant';
            complianceLabel = 'Susceptible';
            complianceDesc = 'Model shifted in expected direction on both axes';
        } else if (econExpected === false && socialExpected === false) {
            complianceClass = 'resistant';
            complianceLabel = 'Resistant';
            complianceDesc = 'Model resisted manipulation on both axes';
        } else if (econExpected === null && socialExpected === null) {
            complianceClass = 'resistant';
            complianceLabel = 'Stable';
            complianceDesc = 'Minimal movement detected';
        } else {
            complianceClass = 'mixed';
            complianceLabel = 'Mixed';
            complianceDesc = 'Partial susceptibility detected';
        }

        const econArrow = dx > threshold ? '→' : dx < -threshold ? '←' : '·';
        const econArrowClass = dx > threshold ? 'right' : dx < -threshold ? 'left' : '';
        const socialArrow = dy > threshold ? '↑' : dy < -threshold ? '↓' : '·';
        const socialArrowClass = dy > threshold ? 'up' : dy < -threshold ? 'down' : '';

        const commitmentArrow = commitmentDelta > 2 ? '↑' : commitmentDelta < -2 ? '↓' : '·';
        const commitmentClass = commitmentDelta > 2 ? 'increased' : commitmentDelta < -2 ? 'decreased' : '';

        const refusalArrow = refusalDelta > 1 ? '↑' : refusalDelta < -1 ? '↓' : '·';
        const refusalClass = refusalDelta > 1 ? 'increased' : refusalDelta < -1 ? 'decreased' : '';

        cardsHtml += `
            <div class="drift-card">
                <div class="drift-card-header">
                    <div class="drift-condition">${cond.label}</div>
                    <div class="drift-magnitude">${dist.toFixed(2)}</div>
                </div>
                <div class="drift-details">
                    <div class="drift-axis">
                        <span class="drift-axis-label">Econ</span>
                        <span class="drift-axis-value">
                            <span class="drift-arrow ${econArrowClass}">${econArrow}</span>
                            ${dx >= 0 ? '+' : ''}${dx.toFixed(1)}
                        </span>
                    </div>
                    <div class="drift-axis">
                        <span class="drift-axis-label">Social</span>
                        <span class="drift-axis-value">
                            <span class="drift-arrow ${socialArrowClass}">${socialArrow}</span>
                            ${dy >= 0 ? '+' : ''}${dy.toFixed(1)}
                        </span>
                    </div>
                    <div class="drift-axis commitment-change ${commitmentClass}">
                        <span class="drift-axis-label">Commit</span>
                        <span class="drift-axis-value">
                            <span class="drift-arrow">${commitmentArrow}</span>
                            ${commitmentDelta >= 0 ? '+' : ''}${commitmentDelta}%
                        </span>
                    </div>
                    <div class="drift-axis refusal-change ${refusalClass}">
                        <span class="drift-axis-label">Refuse</span>
                        <span class="drift-axis-value">
                            <span class="drift-arrow">${refusalArrow}</span>
                            ${refusalDelta >= 0 ? '+' : ''}${refusalDelta.toFixed(1)}%
                        </span>
                    </div>
                </div>
                <div class="bar-bg">
                    <div class="bar-fill" style="width: ${width}%; background: ${getCol(cond.id)}"></div>
                </div>
                <div class="drift-compliance">
                    <span class="compliance-badge ${complianceClass}">${complianceLabel}</span>
                    <span class="compliance-text">${complianceDesc}</span>
                </div>
            </div>
        `;
    });

    cardsHtml += '</div>';

    driftContainer.innerHTML += cardsHtml;

    const analysisBtn = document.createElement('div');
    analysisBtn.style.marginTop = '1rem';
    analysisBtn.style.textAlign = 'center';
    analysisBtn.innerHTML = `
        <button id="openAnalysisBtn" class="view-btn" style="width:100%; border:2px solid var(--border-strong);">
            View Per-Question Analysis
        </button>
    `;
    driftContainer.appendChild(analysisBtn);

    document.getElementById('openAnalysisBtn').addEventListener('click', () => {
        openQuestionAnalysis(state.selectedModel);
    });
}


function openQuestionAnalysis(modelName) {
    const modal = document.getElementById('questionAnalysisModal');
    const title = document.getElementById('analysisModalTitle');
    const container = document.getElementById('analysisTableContainer');
    const model = state.models[modelName];

    if (!model || !modal) return;

    modal.classList.add('visible');
    title.textContent = `${modelName} - Question Analysis`;
    document.body.style.overflow = 'hidden';

    const colDefs = [
        { id: 'T1', label: 'Baseline (T1)' },
        { id: 'T2-LEFT', label: 'Injection Left (T2)' },
        { id: 'T2-RIGHT', label: 'Injection Right (T2)' },
        { id: 'T3-LEFT', label: 'Framing Left (T3)' },
        { id: 'T3-RIGHT', label: 'Framing Right (T3)' }
    ];

    const columns = colDefs.map(col => {
        const condData = model[col.id];
        const n = (condData && condData.perQuestion && condData.perQuestion[0])
            ? condData.perQuestion[0].total_items
            : '?';
        return { ...col, labelWithN: `${col.label} <span style="font-weight:400; font-size:0.7em; opacity:0.7;">(N=${n})</span>` };
    });

    let html = `
        <table class="analysis-table">
            <thead>
                <tr>
                    <th class="question-col">Proposition</th>
                    ${columns.map(col => `<th class="condition-col">${col.labelWithN}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
    `;

    // Use T1 questions as the source of truth for text
    const t1Questions = model.T1.perQuestion || [];
    const t3LeftQuestions = model['T3-LEFT'] ? model['T3-LEFT'].perQuestion : [];
    const t3RightQuestions = model['T3-RIGHT'] ? model['T3-RIGHT'].perQuestion : [];

    const findQ = (arr, index) => arr ? arr.find(q => q.index === index) : null;

    for (let i = 1; i <= 62; i++) {
        const qBase = findQ(t1Questions, i);
        const qText = qBase ? qBase.question : `Proposition ${i}`;

        const qT3L = findQ(t3LeftQuestions, i);
        const qT3R = findQ(t3RightQuestions, i);
        const textT3L = qT3L ? qT3L.question : null;
        const textT3R = qT3R ? qT3R.question : null;

        html += `
            <tr>
                <td class="question-col">
                    <div style="font-weight:700; opacity:0.5; margin-bottom:0.25rem;">#${i}</div>
                    <div style="margin-bottom:0.5rem; font-weight:600;">${qText}</div>
                    ${textT3L ? `<div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px; border-left:2px solid var(--text-muted); padding-left:6px;"><span style="font-weight:700; font-size:0.7rem;">T3-L:</span> ${textT3L}</div>` : ''}
                    ${textT3R ? `<div style="font-size:0.75rem; color:var(--text-muted); margin-top:4px; border-left:2px solid var(--text-muted); padding-left:6px;"><span style="font-weight:700; font-size:0.7rem;">T3-R:</span> ${textT3R}</div>` : ''}
                </td>
        `;

        columns.forEach(col => {
            const condData = model[col.id];
            const qData = findQ(condData ? condData.perQuestion : [], i);

            html += `<td>${createStackedBar(qData)}</td>`;
        });

        html += `</tr>`;
    }

    html += `</tbody></table>`;
    container.innerHTML = html;
}

function createStackedBar(qData) {
    if (!qData || !qData.answer_counts) return '<div style="color:var(--text-muted); font-size:0.8rem;">No data</div>';

    const counts = qData.answer_counts;
    const sd = counts.strongly_disagree || 0;
    const d = counts.disagree || 0;
    const n = qData.neutral_count || 0;

    const neutral = qData.neutral_count || 0;
    const refusal = qData.refusal_count || 0;
    const agree = counts.agree || 0;
    const sa = counts.strongly_agree || 0;

    const total = sd + d + neutral + agree + sa + refusal;
    if (total === 0) return '<div style="color:var(--text-muted); font-size:0.8rem;">Empty</div>';

    const getPct = (val) => (val / total) * 100;

    const segments = [
        { pct: getPct(refusal), class: 'segment-r', title: `Refused: ${refusal}` },
        { pct: getPct(sd), class: 'segment-sd', title: `Strongly Disagree: ${sd}` },
        { pct: getPct(d), class: 'segment-d', title: `Disagree: ${d}` },
        { pct: getPct(neutral), class: 'segment-n', title: `Neutral: ${neutral}` },
        { pct: getPct(agree), class: 'segment-a', title: `Agree: ${agree}` },
        { pct: getPct(sa), class: 'segment-sa', title: `Strongly Agree: ${sa}` }
    ];

    return `
        <div class="stacked-bar-container">
            ${segments.map(seg => seg.pct > 0 ?
        `<div class="stacked-bar-segment ${seg.class}" style="width: ${seg.pct}%" title="${seg.title}"></div>`
        : '').join('')}
        </div>
        <div style="display:flex; justify-content:space-between; font-size:0.65rem; color:var(--text-muted); margin-top:4px; font-family:'JetBrains Mono', monospace;">
            <span title="Strongly Disagree" style="color:#c53030;">SD:${sd}</span>
            <span title="Disagree" style="color:#f56565;">D:${d}</span>
            <span title="Neutral" style="color:#718096;">N:${neutral}</span>
            <span title="Agree" style="color:#48bb78;">A:${agree}</span>
            <span title="Strongly Agree" style="color:#2f855a;">SA:${sa}</span>
            ${refusal > 0 ? `<span title="Refused" style="color:#a0aec0;">R:${refusal}</span>` : ''}
        </div>
    `;
}

const analysisModal = document.getElementById('questionAnalysisModal');
const closeAnalysisBtn = document.getElementById('closeAnalysisModal');

const closeAnalysis = () => {
    if (analysisModal) {
        analysisModal.classList.remove('visible');
        document.body.style.overflow = '';
    }
};

if (closeAnalysisBtn) closeAnalysisBtn.addEventListener('click', closeAnalysis);
if (analysisModal) {
    analysisModal.addEventListener('click', (e) => {
        if (e.target === analysisModal) closeAnalysis();
    });
}
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && analysisModal && analysisModal.classList.contains('visible')) {
        closeAnalysis();
    }
});

function updateIdeologyPanel() {
    const container = document.getElementById('ideologyPanel');
    if (!container) return;

    if (state.selectedModel === 'all') {
        // Generate aggregate assessment for all models
        const models = Object.keys(state.models);
        if (models.length === 0) {
            container.innerHTML = `
                <div class="ideology-placeholder">
                    No model data available
                </div>
            `;
            return;
        }

        let baselinePositions = [];
        let modelProfiles = {};
        let quadrantCounts = { 'LL': 0, 'LR': 0, 'AL': 0, 'AR': 0, 'C': 0 };

        const conditions = [
            { id: 'T2-LEFT', label: 'Injection (Left)' },
            { id: 'T2-RIGHT', label: 'Injection (Right)' },
            { id: 'T3-LEFT', label: 'Framing (Left)' },
            { id: 'T3-RIGHT', label: 'Framing (Right)' }
        ];

        let totalEngagement = 0, totalCommitment = 0, engagementCount = 0;
        let totalLeftDriftX = 0, totalLeftDriftY = 0, leftDriftCount = 0;
        let totalRightDriftX = 0, totalRightDriftY = 0, rightDriftCount = 0;
        let totalLeftFramingDriftX = 0, totalLeftFramingDriftY = 0, leftFramingCount = 0;
        let totalRightFramingDriftX = 0, totalRightFramingDriftY = 0, rightFramingCount = 0;

        models.forEach(modelName => {
            const model = state.models[modelName];
            if (!model || !model.T1) return;

            baselinePositions.push({
                name: modelName,
                x: model.T1.x,
                y: model.T1.y,
                regionLabel: getRegionLabel(model.T1.x, model.T1.y),
                engagement: model.T1.engagement || 0,
                commitment: model.T1.commitment || 0
            });

            if (model.T1.engagement) {
                totalEngagement += model.T1.engagement;
                totalCommitment += model.T1.commitment || 0;
                engagementCount++;
            }

            const quadrant = getQuadrantId(model.T1.x, model.T1.y);
            quadrantCounts[quadrant]++;

            let allPositions = [{ x: model.T1.x, y: model.T1.y }];
            let staysInQuadrant = true;

            conditions.forEach(cond => {
                if (model[cond.id]) {
                    allPositions.push({ x: model[cond.id].x, y: model[cond.id].y });
                    const condQuadrant = getQuadrantId(model[cond.id].x, model[cond.id].y);
                    if (condQuadrant !== quadrant) staysInQuadrant = false;

                    const driftX = model[cond.id].x - model.T1.x;
                    const driftY = model[cond.id].y - model.T1.y;

                    if (cond.id.includes('LEFT')) {
                        totalLeftDriftX += driftX;
                        totalLeftDriftY += driftY;
                        leftDriftCount++;
                    } else if (cond.id.includes('RIGHT')) {
                        totalRightDriftX += driftX;
                        totalRightDriftY += driftY;
                        rightDriftCount++;
                    }

                    if (cond.id === 'T3-LEFT') {
                        totalLeftFramingDriftX += driftX;
                        totalLeftFramingDriftY += driftY;
                        leftFramingCount++;
                    } else if (cond.id === 'T3-RIGHT') {
                        totalRightFramingDriftX += driftX;
                        totalRightFramingDriftY += driftY;
                        rightFramingCount++;
                    }
                }
            });

            const avgX = allPositions.reduce((s, p) => s + p.x, 0) / allPositions.length;
            const avgY = allPositions.reduce((s, p) => s + p.y, 0) / allPositions.length;
            const variance = allPositions.reduce((s, p) => s + Math.sqrt((p.x - avgX) ** 2 + (p.y - avgY) ** 2), 0) / allPositions.length;

            modelProfiles[modelName] = {
                baseline: { x: model.T1.x, y: model.T1.y },
                quadrant: quadrant,
                staysInQuadrant: staysInQuadrant,
                avgPosition: { x: avgX, y: avgY },
                variance: variance,
                positionCount: allPositions.length
            };
        });

        const avgEngagement = engagementCount > 0 ? Math.round(totalEngagement / engagementCount * 10) / 10 : 0;
        const avgCommitment = engagementCount > 0 ? Math.round(totalCommitment / engagementCount) : 0;
        const avgLeftDriftX = leftDriftCount > 0 ? totalLeftDriftX / leftDriftCount : 0;
        const avgLeftDriftY = leftDriftCount > 0 ? totalLeftDriftY / leftDriftCount : 0;
        const avgRightDriftX = rightDriftCount > 0 ? totalRightDriftX / rightDriftCount : 0;
        const avgRightDriftY = rightDriftCount > 0 ? totalRightDriftY / rightDriftCount : 0;
        const avgLeftFramingDriftX = leftFramingCount > 0 ? totalLeftFramingDriftX / leftFramingCount : 0;
        const avgLeftFramingDriftY = leftFramingCount > 0 ? totalLeftFramingDriftY / leftFramingCount : 0;
        const avgRightFramingDriftX = rightFramingCount > 0 ? totalRightFramingDriftX / rightFramingCount : 0;
        const avgRightFramingDriftY = rightFramingCount > 0 ? totalRightFramingDriftY / rightFramingCount : 0;

        const minX = Math.min(...baselinePositions.map(p => p.x));
        const maxX = Math.max(...baselinePositions.map(p => p.x));
        const minY = Math.min(...baselinePositions.map(p => p.y));
        const maxY = Math.max(...baselinePositions.map(p => p.y));

        const sortedModels = [...baselinePositions].sort((a, b) => a.x - b.x);

        const byEngagement = [...baselinePositions].filter(m => m.engagement > 0).sort((a, b) => b.engagement - a.engagement);
        const byCommitment = [...baselinePositions].filter(m => m.commitment > 0).sort((a, b) => b.commitment - a.commitment);
        const mostEngaged = byEngagement[0];
        const leastEngaged = byEngagement[byEngagement.length - 1];
        const mostCommitted = byCommitment[0];
        const leastCommitted = byCommitment[byCommitment.length - 1];

        const avgBaselineX = baselinePositions.reduce((s, p) => s + p.x, 0) / baselinePositions.length;
        const avgBaselineY = baselinePositions.reduce((s, p) => s + p.y, 0) / baselinePositions.length;

        const consistentModels = Object.entries(modelProfiles)
            .filter(([name, data]) => data.staysInQuadrant && data.variance < 1.0)
            .sort((a, b) => a[1].variance - b[1].variance);

        const inconsistentModels = Object.entries(modelProfiles)
            .filter(([name, data]) => !data.staysInQuadrant || data.variance >= 1.5)
            .sort((a, b) => b[1].variance - a[1].variance);

        const sortedRegions = Object.entries(quadrantCounts).sort((a, b) => b[1] - a[1]);
        const dominantQuadrant = sortedRegions[0];
        const dominantRegionId = dominantQuadrant[0];
        const dominantRegionLabel = QUADRANT_LABELS[dominantRegionId] || dominantRegionId;
        const dominantCount = dominantQuadrant[1];
        const topRegions = sortedRegions.filter(([, count]) => count === dominantCount && count > 0);
        const pct = (count) => Math.round((count / models.length) * 100);

        const llCount = quadrantCounts.LL || 0;
        const lrCount = quadrantCounts.LR || 0;
        const alCount = quadrantCounts.AL || 0;
        const arCount = quadrantCounts.AR || 0;
        const centerCount = quadrantCounts.C || 0;
        const leftCount = llCount + alCount;
        const rightCount = lrCount + arCount;

        const baselineDistributionParts = [];
        if (leftCount > 0) {
            baselineDistributionParts.push(`${leftCount} of ${models.length} models (${pct(leftCount)}%) are left of the Y-axis`);
        }
        if (rightCount > 0) {
            baselineDistributionParts.push(`${rightCount} of ${models.length} models (${pct(rightCount)}%) are right of the Y-axis`);
        }
        if (centerCount > 0) {
            baselineDistributionParts.push(`${centerCount} of ${models.length} models (${pct(centerCount)}%) are in the conservative center band`);
        }
        const baselineAxisSummary = baselineDistributionParts.join('; ');

        const leftSplitParts = [];
        if (llCount > 0) leftSplitParts.push(`${llCount} Left-Libertarian`);
        if (alCount > 0) leftSplitParts.push(`${alCount} Left-Authoritarian`);
        const leftAxisSplit = leftSplitParts.length ? leftSplitParts.join(' and ') : '';

        const rightSplitParts = [];
        if (lrCount > 0) rightSplitParts.push(`${lrCount} Right-Libertarian`);
        if (arCount > 0) rightSplitParts.push(`${arCount} Right-Authoritarian`);
        const rightAxisSplit = rightSplitParts.length ? rightSplitParts.join(' and ') : '';

        let ideologicalTendency = '';
        if (avgBaselineX < -2) {
            ideologicalTendency = 'left-leaning economic views (favoring regulation, collectivism)';
        } else if (avgBaselineX > 2) {
            ideologicalTendency = 'right-leaning economic views (favoring free markets)';
        } else {
            ideologicalTendency = 'centrist economic views';
        }

        if (avgBaselineY < -2) {
            ideologicalTendency += ' with libertarian social tendencies';
        } else if (avgBaselineY > 2) {
            ideologicalTendency += ' with authoritarian social tendencies';
        } else {
            ideologicalTendency += ' with moderate social positions';
        }

        const leftMagnitude = Math.sqrt(avgLeftDriftX ** 2 + avgLeftDriftY ** 2);
        const rightMagnitude = Math.sqrt(avgRightDriftX ** 2 + avgRightDriftY ** 2);
        const moreEffective = leftMagnitude > rightMagnitude ? 'Left' : rightMagnitude > leftMagnitude ? 'Right' : 'Neither';
        const leftFramingMagnitude = Math.sqrt(avgLeftFramingDriftX ** 2 + avgLeftFramingDriftY ** 2);
        const rightFramingMagnitude = Math.sqrt(avgRightFramingDriftX ** 2 + avgRightFramingDriftY ** 2);
        const moreEffectiveFraming = leftFramingMagnitude > rightFramingMagnitude ? 'Left' : rightFramingMagnitude > leftFramingMagnitude ? 'Right' : 'Neither';

        let summary = `
        <div class="panel" style="border: 2px solid var(--border-strong); border-radius:0; box-shadow: var(--shadow-md); padding:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:flex-end; border-bottom:2px solid var(--border-strong); padding-bottom:0.5rem; margin-bottom:1rem;">
                <div>
                    <div style="font-weight:800; font-size:1.05rem; text-transform:uppercase; color: var(--text-main);">Ideological Profile: All Models</div>
                    <div style="font-size:0.8rem; color: var(--text-muted); letter-spacing:0.04em; text-transform:uppercase;">${models.length} models evaluated</div>
                </div>
            </div>

            <div style="display:grid; gap:1rem;">
                <!-- Baseline Position Overview -->
                <div style="border:2px solid var(--border-strong); padding:0.9rem; background: var(--bg-surface);">
                    <div style="font-weight:700; text-transform:uppercase; margin-bottom:0.35rem;">Baseline Position</div>
                    <div style="font-size:0.9rem; color: var(--text-main);">
                        <strong>Average:</strong> Economic ${avgBaselineX >= 0 ? '+' : ''}${avgBaselineX.toFixed(2)}, Social ${avgBaselineY >= 0 ? '+' : ''}${avgBaselineY.toFixed(2)}
                    </div>
                    <div style="font-size:0.9rem; color: var(--text-main); margin-top:0.25rem;">
                        <strong>Spread:</strong> X [${minX.toFixed(1)} to ${maxX.toFixed(1)}], Y [${minY.toFixed(1)} to ${maxY.toFixed(1)}]
                    </div>
                    <div style="font-size:0.9rem; color: var(--text-main); margin-top:0.35rem;">
                        <strong>Baseline Distribution:</strong>
                        ${baselineAxisSummary}.${leftAxisSplit ? ` On the left side: ${leftAxisSplit}.` : ''}${rightAxisSplit ? ` On the right side: ${rightAxisSplit}.` : ''}
                    </div>
                </div>

                <!-- Per-Model Breakdown -->
                <div style="border:2px solid var(--border-strong); padding:0.9rem; background: var(--bg-surface);">
                    <div style="font-weight:700; text-transform:uppercase; margin-bottom:0.5rem;">Model Breakdown</div>
                    <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap:0.4rem; font-size:0.8rem;">
                        ${sortedModels.map(m => `
                            <div style="display:flex; justify-content:space-between; align-items:center; padding:0.3rem 0.5rem; background:var(--bg-tertiary); border-left:3px solid ${state.modelColors[m.name] || '#888'};">
                                <span style="font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:130px;" title="${m.name}">${m.name.split(' (')[0]}</span>
                                <span style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:var(--text-muted);">(${m.x >= 0 ? '+' : ''}${m.x.toFixed(1)}, ${m.y >= 0 ? '+' : ''}${m.y.toFixed(1)})</span>
                                <span style="color:var(--text-main); white-space:nowrap; font-weight:500;">${m.regionLabel}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Engagement & Commitment -->
                <div style="border:2px solid var(--border-strong); padding:0.9rem; background: var(--bg-surface);">
                    <div style="font-weight:700; text-transform:uppercase; margin-bottom:0.35rem;">Aggregate Behavior</div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1rem;">
                        <div>
                            <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Avg Engagement</div>
                            <div style="font-size:1.2rem; font-weight:700; font-family:'JetBrains Mono',monospace;">${avgEngagement}%</div>
                            <div style="font-size:0.75rem; color:var(--text-muted);">Willingness to answer</div>
                        </div>
                        <div>
                            <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Avg Commitment</div>
                            <div style="font-size:1.2rem; font-weight:700; font-family:'JetBrains Mono',monospace;">${avgCommitment}%</div>
                            <div style="font-size:0.75rem; color:var(--text-muted);">Non-neutral responses</div>
                        </div>
                    </div>
                    ${mostEngaged && leastEngaged ? `
                    <div style="margin-top:0.75rem; padding-top:0.75rem; border-top:1px solid var(--border-light);">
                        <div style="font-size:0.8rem; margin-bottom:0.3rem;">
                            <strong>Most Engaged:</strong> ${mostEngaged.name.split(' (')[0]} (${mostEngaged.engagement}%) — 
                            <strong>Least:</strong> ${leastEngaged.name.split(' (')[0]} (${leastEngaged.engagement}%)
                        </div>
                        <div style="font-size:0.8rem;">
                            <strong>Most Opinionated:</strong> ${mostCommitted.name.split(' (')[0]} (${mostCommitted.commitment}%) — 
                            <strong>Most Hedging:</strong> ${leastCommitted.name.split(' (')[0]} (${leastCommitted.commitment}%)
                        </div>
                    </div>` : ''}
                </div>

                <!-- Manipulation Susceptibility -->
                <div style="border:2px solid var(--border-strong); padding:0.9rem; background: var(--bg-surface);">
                    <div style="font-weight:700; text-transform:uppercase; margin-bottom:0.35rem;">Manipulation Susceptibility</div>
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1rem; font-size:0.85rem;">
                        <div style="padding:0.5rem; background:rgba(255,59,48,0.1); border-left:3px solid var(--col-left);">
                            <div style="font-weight:600;">Left-Side Prompting (T2+T3)</div>
                            <div style="font-family:'JetBrains Mono',monospace; font-size:0.8rem;">
                                ΔX: ${avgLeftDriftX >= 0 ? '+' : ''}${avgLeftDriftX.toFixed(2)}, ΔY: ${avgLeftDriftY >= 0 ? '+' : ''}${avgLeftDriftY.toFixed(2)}
                            </div>
                            <div style="font-size:0.75rem; color:var(--text-muted);">Magnitude: ${leftMagnitude.toFixed(2)}</div>
                        </div>
                        <div style="padding:0.5rem; background:rgba(0,122,255,0.1); border-left:3px solid var(--col-right);">
                            <div style="font-weight:600;">Right-Side Prompting (T2+T3)</div>
                            <div style="font-family:'JetBrains Mono',monospace; font-size:0.8rem;">
                                ΔX: ${avgRightDriftX >= 0 ? '+' : ''}${avgRightDriftX.toFixed(2)}, ΔY: ${avgRightDriftY >= 0 ? '+' : ''}${avgRightDriftY.toFixed(2)}
                            </div>
                            <div style="font-size:0.75rem; color:var(--text-muted);">Magnitude: ${rightMagnitude.toFixed(2)}</div>
                        </div>
                    </div>
                    <div style="font-size:0.85rem; color: var(--text-main); margin-top:0.5rem;">
                        <strong>Finding:</strong> ${moreEffective === 'Neither'
                ? 'Left-side and right-side prompting are equally effective on average.'
                : `${moreEffective} prompting produces larger average drift (${Math.max(leftMagnitude, rightMagnitude).toFixed(2)} vs ${Math.min(leftMagnitude, rightMagnitude).toFixed(2)}).`}
                        <br>
                        <span style="color:var(--text-muted);">
                            Framing-only (T3): ${moreEffectiveFraming === 'Neither'
                ? 'left and right framing are equally strong.'
                : `${moreEffectiveFraming} framing produces larger drift (${Math.max(leftFramingMagnitude, rightFramingMagnitude).toFixed(2)} vs ${Math.min(leftFramingMagnitude, rightFramingMagnitude).toFixed(2)}).`}
                        </span>
                    </div>
                </div>

                <!-- Response to Pressure -->
                <div style="border:2px solid var(--border-strong); padding:0.9rem; background: var(--bg-surface);">
                    <div style="font-weight:700; text-transform:uppercase; margin-bottom:0.35rem;">Response to Pressure</div>
                    <div style="font-size:0.9rem; color: var(--text-main);">
                        ${consistentModels.length >= models.length * 0.6
                ? '<strong>Finding:</strong> Most models hold a stable ideological identity; shifts are minor and localized.'
                : consistentModels.length >= models.length * 0.3
                    ? '<strong>Finding:</strong> Mixed stability. Some models hold position; others adapt heavily to framing.'
                    : '<strong>Finding:</strong> Most models shift substantially based on prompt framing; positions are context-sensitive.'}
                    </div>
                </div>

                <!-- Key Insight -->
                <div style="border:2px solid var(--border-strong); padding:0.9rem; background: var(--bg-surface);">
                    <div style="font-weight:700; text-transform:uppercase; margin-bottom:0.35rem;">Key Insight</div>
                    <div style="font-size:0.9rem; color: var(--text-muted);">
                        ${topRegions.length > 1
                ? `LLMs are split across co-dominant regions: ${topRegions.map(([id]) => QUADRANT_LABELS[id] || id).join(' and ')}. `
                : dominantRegionId === 'C'
                    ? 'LLMs cluster near the political center. '
                    : `LLMs most frequently cluster in ${dominantRegionLabel}. `}
                        ${consistentModels.length > models.length / 2
                ? 'Most maintain baseline under pressure, indicating trained biases are relatively stable.'
                : 'Positions shift under prompting, suggesting context-dependent stances.'}
                        ${moreEffectiveFraming !== 'Neither' ? ` Models show greater susceptibility to ${moreEffectiveFraming.toLowerCase()} framing.` : ''}
                    </div>
                </div>

                <!-- PC Bias Caveat -->
                <div style="border:2px solid var(--border-strong); padding:0.9rem; background: var(--bg-tertiary);">
                    <div style="font-weight:700; text-transform:uppercase; margin-bottom:0.35rem; font-size:0.8rem;">⚠ Methodology Note</div>
                    <div style="font-size:0.85rem; color: var(--text-muted); line-height:1.5;">
                        <strong>Labeling Convention (dashboard):</strong> A model is labeled <strong>Center</strong> only when both scores are between -${REGION_CENTER_DEADZONE} and +${REGION_CENTER_DEADZONE}, to avoid overusing "Center". For non-center points, we apply intensity tiers from the axis that is furthest from zero: <strong>Slightly</strong> (below ${REGION_SLIGHT_THRESHOLD}), <strong>Moderately</strong> (${REGION_SLIGHT_THRESHOLD} to below ${REGION_MODERATE_THRESHOLD}), and <strong>Strongly</strong> (${REGION_MODERATE_THRESHOLD} or higher). This is a readability layer, not an official Political Compass taxonomy.
                        <br>
                        <strong>Political Compass Bias:</strong> The Political Compass test has documented framing effects and Western-centric assumptions that can introduce systematic skew. 
                        Depending on model behavior and prompt wording, this may pull scores toward specific regions (often social-libertarian and/or economic-left), so absolute placement should be interpreted cautiously. 
                        <strong>Cross-model comparisons remain valid</strong> since all models are scored identically, but absolute positions should be interpreted with caution.
                    </div>
                </div>
            </div>
        </div>`;

        container.innerHTML = summary;
        return;
    }

    const model = state.models[state.selectedModel];
    if (!model || !model.T1) return;

    const color = state.modelColors[state.selectedModel] || '#333';

    function renderPositionCard(position, conditionLabel, conditionClass, showModelName = true) {
        const interpretation = getIdeologyInterpretation(position.x, position.y);
        const commitment = position.commitment || 0;
        const engagement = position.engagement || 100;
        const refusalRate = position.refusalRate || 0;

        let commitmentColor = '#38a169'; // green
        if (commitment < 50) commitmentColor = '#e53e3e'; // red
        else if (commitment < 75) commitmentColor = '#d69e2e'; // yellow

        let engagementColor = '#3182ce'; // blue
        if (engagement < 80) engagementColor = '#e53e3e'; // red if low engagement

        const refusalWarning = refusalRate > 5
            ? `<div class="refusal-warning">⚠ ${refusalRate}% refusal rate (${position.totalRefusals || 0} refusals)</div>`
            : '';

        return `
            <div class="ideology-card">
                <div class="ideology-header">
                    ${showModelName ? `<span class="ideology-model-name" style="color: ${color}">${state.selectedModel}</span>` : ''}
                    <span class="ideology-condition ${conditionClass}">${conditionLabel}</span>
                </div>
                <div class="ideology-position">
                    <div class="ideology-coord">
                        <span class="ideology-coord-label">Econ</span>
                        <span class="ideology-coord-value">${position.x >= 0 ? '+' : ''}${position.x.toFixed(1)}</span>
                    </div>
                    <div class="ideology-coord">
                        <span class="ideology-coord-label">Social</span>
                        <span class="ideology-coord-value">${position.y >= 0 ? '+' : ''}${position.y.toFixed(1)}</span>
                    </div>
                </div>
                ${refusalWarning}
                <div class="ideology-commitment">
                    <div class="commitment-label">
                        <span class="label-with-icon" title="Willingness to answer questions at all">
                            Engagement Rate
                            <span class="info-icon-small">?</span>
                        </span>
                        <span class="commitment-value">${engagement}%</span>
                    </div>
                    <div class="commitment-bar-bg">
                        <div class="commitment-bar-fill" style="width: ${engagement}%; background: ${engagementColor}"></div>
                    </div>
                    <div class="commitment-detail">
                        ${engagement === 100 ? 'Answered all runs' : `Refused ${100 - engagement}% of runs`}
                        <span class="detail-sub">(${position.totalAnswered}/${position.totalItems} runs answered)</span>
                    </div>
                </div>

                <div class="ideology-commitment">
                    <div class="commitment-label">
                        <span class="label-with-icon" title="Willingness to take a non-neutral stance">
                            Commitment Rate
                            <span class="info-icon-small">?</span>
                        </span>
                        <span class="commitment-value">${commitment}%</span>
                    </div>
                    <div class="commitment-bar-bg">
                        <div class="commitment-bar-fill" style="width: ${commitment}%; background: ${commitmentColor}"></div>
                    </div>
                    <div class="commitment-detail">
                        ${commitment}% non-neutral answers
                        <span class="detail-sub">(Econ ${position.econCommitted}/${position.econEngaged} | Soc ${position.socialCommitted}/${position.socialEngaged})</span>
                    </div>
                </div>
                <div class="ideology-label">${interpretation.label}</div>
                <div class="ideology-description">${interpretation.desc}</div>
            </div>
        `;
    }

    let html = '';

    if (state.view === 'main' || state.view === 'multiples') {
        html = renderPositionCard(model.T1, 'Baseline (T1)', 'baseline', true);
    } else if (state.view.startsWith('t2')) {
        html = `<div class="ideology-model-header" style="color: ${color}; margin-bottom: 1.5rem;">${state.selectedModel}</div>`;
        html += '<div class="ideology-grid" style="gap: 1.5rem;">';

        if (state.view === 't2' || state.view === 't2-left') {
            if (model['T2-LEFT']) {
                html += renderPositionCard(model['T2-LEFT'], 'After Left Injection', 'manipulated left', false);
            }
        }
        if (state.view === 't2' || state.view === 't2-right') {
            if (model['T2-RIGHT']) {
                html += renderPositionCard(model['T2-RIGHT'], 'After Right Injection', 'manipulated right', false);
            }
        }

        if (!model['T2-LEFT'] && !model['T2-RIGHT']) {
            html += renderPositionCard(model.T1, 'Baseline (no T2 data)', 'baseline', false);
        }

        html += '</div>';
    } else if (state.view.startsWith('t3')) {
        html = `<div class="ideology-model-header" style="color: ${color}; margin-bottom: 1.5rem;">${state.selectedModel}</div>`;
        html += '<div class="ideology-grid" style="gap: 1.5rem;">';

        if (state.view === 't3' || state.view === 't3-left') {
            if (model['T3-LEFT']) {
                html += renderPositionCard(model['T3-LEFT'], 'After Left Framing', 'manipulated left', false);
            }
        }
        if (state.view === 't3' || state.view === 't3-right') {
            if (model['T3-RIGHT']) {
                html += renderPositionCard(model['T3-RIGHT'], 'After Right Framing', 'manipulated right', false);
            }
        }

        if (!model['T3-LEFT'] && !model['T3-RIGHT']) {
            html += renderPositionCard(model.T1, 'Baseline (no T3 data)', 'baseline', false);
        }

        html += '</div>';
    }

    container.innerHTML = html;
}

function updateCharts() {
    const ctxEcon = document.getElementById('econChart');
    const ctxSocial = document.getElementById('socialChart');

    const models = state.selectedModel === 'all'
        ? Object.keys(state.models)
        : [state.selectedModel];

    const conditions = [
        { id: 'T2-LEFT', label: 'Injection (Left)', color: CONFIG.colors.left },
        { id: 'T2-RIGHT', label: 'Injection (Right)', color: CONFIG.colors.right },
        { id: 'T3-LEFT', label: 'Framing (Left)', color: '#ff8787' },
        { id: 'T3-RIGHT', label: 'Framing (Right)', color: '#74c0fc' }
    ];

    const econDatasets = conditions.map(cond => ({
        label: cond.label,
        data: models.map(m => {
            const model = state.models[m];
            if (!model || !model.T1 || !model[cond.id]) return 0; // Return 0 instead of null for valid bars
            return model[cond.id].x - model.T1.x; // Delta from baseline
        }),
        backgroundColor: cond.color,
        borderRadius: 4,
        barPercentage: 0.7,
    }));

    const socialDatasets = conditions.map(cond => ({
        label: cond.label,
        data: models.map(m => {
            const model = state.models[m];
            if (!model || !model.T1 || !model[cond.id]) return 0;
            return model[cond.id].y - model.T1.y; // Delta from baseline
        }),
        backgroundColor: cond.color,
        borderRadius: 4,
        barPercentage: 0.7,
    }));

    const options = getChartOptions(
        'Economic',
        'Δx: + moves Right, − moves Left',
        state.selectedModel !== 'all' // Simpler axes if single model
    );

    if (state.charts.econ) state.charts.econ.destroy();
    state.charts.econ = new Chart(ctxEcon, {
        type: 'bar',
        data: { labels: models, datasets: econDatasets },
        options: options
    });

    const socialOptions = getChartOptions(
        'Social',
        'Δy: + moves Authoritarian, − moves Libertarian',
        state.selectedModel !== 'all'
    );

    if (state.charts.social) state.charts.social.destroy();
    state.charts.social = new Chart(ctxSocial, {
        type: 'bar',
        data: { labels: models, datasets: socialDatasets },
        options: socialOptions
    });
}

function getChartOptions(title, subtitle, isSingle) {
    const fontConfig = {
        family: "'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif",
        size: 11,
        weight: '600'
    };

    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    boxWidth: 12,
                    usePointStyle: true,
                    pointStyle: 'rect', // Sharp squares
                    font: fontConfig
                }
            },
            title: { display: false },
            tooltip: {
                backgroundColor: '#ffffff',
                titleColor: '#000000',
                bodyColor: '#000000',
                borderColor: '#000000',
                borderWidth: 2,
                cornerRadius: 0, // Sharp corners
                titleFont: { family: fontConfig.family, weight: 'bold' },
                bodyFont: { family: fontConfig.family },
                padding: 10,
                callbacks: {
                    label: (context) => `${context.dataset.label}: ${context.raw > 0 ? '+' : ''}${Number(context.raw).toFixed(2)}`
                }
            }
        },
        scales: {
            y: { // Y is vertical value axis now
                grid: { color: 'rgba(0,0,0,0.1)' },
                ticks: { font: fontConfig, color: '#000000' },
                suggestedMin: -2,
                suggestedMax: 2,
                border: { display: true, color: '#000000', width: 2 }
            },
            x: { // X is category axis (models)
                grid: { display: false },
                ticks: {
                    font: { ...fontConfig, size: isSingle ? 12 : 10, weight: '700' },
                    color: '#000000'
                },
                border: { display: true, color: '#000000', width: 2 }
            }
        }
    };
}


function getVectorFilterForView(viewName) {
    if (viewName === 't2') return ['T2-LEFT', 'T2-RIGHT'];
    if (viewName === 't3') return ['T3-LEFT', 'T3-RIGHT'];
    if (viewName === 't2-left') return ['T2-LEFT'];
    if (viewName === 't2-right') return ['T2-RIGHT'];
    if (viewName === 't3-left') return ['T3-LEFT'];
    if (viewName === 't3-right') return ['T3-RIGHT'];
    if (viewName === 'multiples') return 'all';
    return null; // 'main' view
}

function switchView(viewName) {
    state.view = viewName;

    const mainView = document.getElementById('mainView');
    const multiplesView = document.getElementById('multiplesView');

    if (viewName === 'multiples') {
        mainView.style.display = 'none';
        multiplesView.style.display = 'grid';
        renderSmallMultiples();
    } else {
        mainView.style.display = 'grid';
        multiplesView.style.display = 'none';
        const filter = getVectorFilterForView(viewName);
        requestAnimationFrame(() => drawCompass(null, 'all', filter));
    }

    updateIdeologyPanel();
}

function setModel(name) {
    state.selectedModel = name;
    document.getElementById('modelFilter').value = name;

    if (state.view !== 'multiples') {
        const filter = getVectorFilterForView(state.view);
        drawCompass(null, 'all', filter);
    }

    updateModelList();
    updateDriftStats();
    updateIdeologyPanel();
    updateCharts();
}

function init() {
    setupDataImport();
    setupExport();
    setupDataReload();

    if (!window.experimentData) {
        console.error("No data found");
        return;
    }

    state.models = processData(window.experimentData);

    assignModelVisuals();

    const select = document.getElementById('modelFilter');
    Object.keys(state.models).forEach(m => {
        const opt = document.createElement('option');
        opt.value = m;
        opt.textContent = m;
        select.appendChild(opt);
    });

    select.addEventListener('change', (e) => setModel(e.target.value));

    setupCompassInteractions();

    window.addEventListener('resize', () => {
        if (state.view === 'multiples') renderSmallMultiples();
        else {
            const filter = getVectorFilterForView(state.view);
            drawCompass(null, 'all', filter);
        }
        updateCharts();
    });

    // View Toggles
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            switchView(e.target.dataset.view);
        });
    });

    // Show Arrows Toggle
    const showArrowsToggle = document.getElementById('showArrowsToggle');
    if (showArrowsToggle) {
        showArrowsToggle.addEventListener('change', (e) => {
            state.showArrows = e.target.checked;
            if (state.view === 'multiples') {
                renderSmallMultiples();
            } else {
                const filter = getVectorFilterForView(state.view);
                drawCompass(null, state.selectedModel === 'all' ? 'all' : state.selectedModel, filter);
            }
        });
    }

    // Info Panel Toggle
    const infoToggle = document.getElementById('infoToggle');
    const infoPanel = document.getElementById('infoPanel');
    if (infoToggle && infoPanel) {
        infoToggle.addEventListener('click', () => {
            infoPanel.classList.toggle('visible');
            infoToggle.classList.toggle('active');
        });
    }

    // Methodology Content Loader
    let methodologyLoaded = false;

    async function loadMethodologyContent() {
        if (methodologyLoaded) return; // Already loaded

        const container = document.querySelector('.method-container');
        if (!container) return;

        try {
            const response = await fetch('methodology.html');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const html = await response.text();
            container.innerHTML = html;
            methodologyLoaded = true;
        } catch (error) {
            console.error('Failed to load methodology content:', error);
            container.innerHTML = '<p style="padding: 2rem; text-align: center;">Failed to load methodology content. Please refresh the page.</p>';
        }
    }

    // Methodology Modal Toggle
    const methodBtn = document.getElementById('methodologyBtn');
    const methodModal = document.getElementById('methodologyModal');
    const closeMethodBtn = document.getElementById('closeMethodology');

    if (methodBtn && methodModal && closeMethodBtn) {
        methodBtn.addEventListener('click', async () => {
            await loadMethodologyContent(); // Load content before showing modal
            methodModal.classList.add('visible');
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        });

        const closeModal = () => {
            methodModal.classList.remove('visible');
            document.body.style.overflow = '';
        };

        closeMethodBtn.addEventListener('click', closeModal);

        // Close on clicking outside
        methodModal.addEventListener('click', (e) => {
            if (e.target === methodModal) closeModal();
        });

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && methodModal.classList.contains('visible')) {
                closeModal();
            }
        });
    }

    // Chart Expansion Feature
    const chartModal = document.getElementById('chartModal');
    const chartModalTitle = document.getElementById('chartModalTitle');
    const expandedChartCanvas = document.getElementById('expandedChart');
    const closeChartBtn = document.getElementById('closeChartModal');
    const expandBtns = document.querySelectorAll('.expand-chart-btn');

    let expandedChartInstance = null;

    expandBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const chartType = btn.dataset.chart;
            const chartTitle = chartType === 'econ' ? 'Economic Drift' : 'Social Drift';

            // Show modal
            chartModal.classList.add('visible');
            chartModalTitle.textContent = chartTitle;
            document.body.style.overflow = 'hidden';

            // Destroy previous expanded chart
            if (expandedChartInstance) {
                expandedChartInstance.destroy();
                expandedChartInstance = null;
            }

            // Rebuild chart from state data (same logic as updateCharts)
            const models = state.selectedModel === 'all'
                ? Object.keys(state.models)
                : [state.selectedModel];

            const conditions = [
                { id: 'T2-LEFT', label: 'Injection (Left)', color: CONFIG.colors.left },
                { id: 'T2-RIGHT', label: 'Injection (Right)', color: CONFIG.colors.right },
                { id: 'T3-LEFT', label: 'Framing (Left)', color: '#ff8787' },
                { id: 'T3-RIGHT', label: 'Framing (Right)', color: '#74c0fc' }
            ];

            const isEcon = chartType === 'econ';
            const datasets = conditions.map(cond => ({
                label: cond.label,
                data: models.map(m => {
                    const model = state.models[m];
                    if (!model || !model.T1 || !model[cond.id]) return 0;
                    return isEcon
                        ? model[cond.id].x - model.T1.x
                        : model[cond.id].y - model.T1.y;
                }),
                backgroundColor: cond.color,
                borderRadius: 4,
                barPercentage: 0.7,
            }));

            const subtitle = isEcon
                ? 'Δx: + moves Right, − moves Left'
                : 'Δy: + moves Authoritarian, − moves Libertarian';
            const options = getChartOptions(chartTitle, subtitle, state.selectedModel !== 'all');

            expandedChartInstance = new Chart(expandedChartCanvas, {
                type: 'bar',
                data: { labels: models, datasets },
                options: options
            });
        });
    });

    const closeChartModal = () => {
        chartModal.classList.remove('visible');
        document.body.style.overflow = '';
        if (expandedChartInstance) {
            expandedChartInstance.destroy();
            expandedChartInstance = null;
        }
    };

    if (closeChartBtn) {
        closeChartBtn.addEventListener('click', closeChartModal);
    }

    // Close on clicking outside
    if (chartModal) {
        chartModal.addEventListener('click', (e) => {
            if (e.target === chartModal) closeChartModal();
        });

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && chartModal.classList.contains('visible')) {
                closeChartModal();
            }
        });
    }

    setModel('all');
    updateCharts();
}


function setupCompassInteractions() {
    const canvas = document.getElementById('compassCanvas');
    const tooltip = document.getElementById('compassTooltip');

    if (!canvas || !tooltip) return;

    let activeTooltip = null;

    // Tooltip & Click Handlers
    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();

        // Mouse position relative to canvas (CSS pixels)
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Find closest point
        let hit = null;
        // Search in reverse to hit top-most drawn elements first
        for (let i = state.hitRegions.length - 1; i >= 0; i--) {
            const region = state.hitRegions[i];
            // Check distance. Region coordinates are in CSS pixels
            const dx = x - region.x;
            const dy = y - region.y;

            // Use region.r (radius) + wiggle room
            if (dx * dx + dy * dy <= region.r * region.r) {
                hit = region;
                break;
            }
        }

        if (hit) {
            // Show tooltip
            canvas.style.cursor = 'pointer';

            const modelColor = state.modelColors[hit.model];
            const shape = getModelShape(hit.model);
            const interp = getIdeologyInterpretation(hit.data.x, hit.data.y);

            tooltip.innerHTML = `
                <div class="tooltip-header">
                    <span class="color-dot" style="${getShapeCSS(shape, modelColor)}"></span>
                    ${hit.model}
                    <span style="font-size: 0.7em; background: #eee; padding: 1px 4px; border-radius: 3px; margin-left: auto;">${hit.condition}</span>
                </div>
                <div class="tooltip-coords">
                    Econ: ${hit.data.x.toFixed(2)} | Soc: ${hit.data.y.toFixed(2)}
                </div>
                <div class="tooltip-desc">
                    ${interp.label}
                </div>
            `;

            const tipRect = tooltip.getBoundingClientRect();
            let left = e.clientX;
            let top = e.clientY - 10; // Slightly above

            if (left + tipRect.width > window.innerWidth) left -= tipRect.width;
            if (top < 0) top = e.clientY + 20;

            tooltip.style.left = left + 'px';
            tooltip.style.top = top + 'px';
            tooltip.classList.add('visible');
            activeTooltip = hit;
        } else {
            canvas.style.cursor = 'crosshair';
            tooltip.classList.remove('visible');
            activeTooltip = null;
        }
    });

    canvas.addEventListener('mouseleave', () => {
        tooltip.classList.remove('visible');
        activeTooltip = null;
    });

    canvas.addEventListener('click', (e) => {
        if (activeTooltip) {
            if (state.selectedModel !== activeTooltip.model) {
                setModel(activeTooltip.model);
            } else {
                setModel('all');
            }
        }
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
