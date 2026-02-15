const vscode = acquireVsCodeApi();
const boot = window.__CHTHONIC_ABYSSAL__ || {};

const canvas = /** @type {HTMLCanvasElement} */ (document.getElementById('graph-canvas'));
const statFiles = document.getElementById('stat-files');
const statEntropy = document.getElementById('stat-entropy');
const statRenderer = document.getElementById('stat-renderer');

let wasmRenderGraph = null;
let latestGraph = null;
let projectedNodes = [];

function clamp01(value) {
    return Math.max(0, Math.min(1, value));
}

function parseCssColor(value) {
    if (!value) return null;
    const raw = value.trim();
    if (raw.startsWith('#')) {
        let hex = raw.slice(1);
        if (hex.length === 3) {
            hex = hex.split('').map((ch) => ch + ch).join('');
        }
        if (hex.length < 6) return null;
        return [
            parseInt(hex.slice(0, 2), 16),
            parseInt(hex.slice(2, 4), 16),
            parseInt(hex.slice(4, 6), 16),
        ];
    }
    const rgbMatch = raw.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/i);
    if (rgbMatch) {
        return [Number(rgbMatch[1]), Number(rgbMatch[2]), Number(rgbMatch[3])];
    }
    return null;
}

function mix(a, b, t) {
    return Math.round((a * (1 - t)) + (b * t));
}

function toCss(rgb) {
    return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}

function sepiaShift(rgb, darkness) {
    const sepia = [112, 93, 68];
    const factor = clamp01((darkness * 0.55) + 0.15);
    return [
        mix(rgb[0], sepia[0], factor),
        mix(rgb[1], sepia[1], factor),
        mix(rgb[2], sepia[2], factor),
    ];
}

function darken(rgb, darkness) {
    const factor = 1 - (darkness * 0.28);
    return rgb.map((channel) => Math.round(channel * factor));
}

function computeDarkness() {
    const now = new Date();
    const hour = now.getHours() + (now.getMinutes() / 60);
    const daylight = (Math.cos(((hour - 12) / 12) * Math.PI) + 1) / 2;
    return clamp01(1 - daylight);
}

function applyCircadianTheme() {
    const css = getComputedStyle(document.documentElement);
    const baseBg = parseCssColor(css.getPropertyValue('--vscode-editor-background')) || [19, 15, 12];
    const basePanel = parseCssColor(css.getPropertyValue('--vscode-editorWidget-background')) || [30, 24, 20];
    const baseFg = parseCssColor(css.getPropertyValue('--vscode-editor-foreground')) || [226, 215, 205];

    const darkness = computeDarkness();
    const shiftedBg = darken(sepiaShift(baseBg, darkness), darkness);
    const shiftedPanel = darken(sepiaShift(basePanel, darkness), darkness * 0.85);
    const shiftedFg = sepiaShift(baseFg, darkness * 0.25);
    const accent = sepiaShift([201, 169, 98], darkness * 0.45);

    document.documentElement.style.setProperty('--abyss-bg', toCss(shiftedBg));
    document.documentElement.style.setProperty('--abyss-panel', toCss(shiftedPanel));
    document.documentElement.style.setProperty('--abyss-fg', toCss(shiftedFg));
    document.documentElement.style.setProperty('--abyss-accent', toCss(accent));
}

function entropyColor(entropy) {
    if (entropy >= 0.78) return '#8a4c2a';
    if (entropy >= 0.48) return '#c9a962';
    return '#7cae67';
}

function computeProjection(graph) {
    const width = Math.max(320, canvas.clientWidth);
    const height = Math.max(220, canvas.clientHeight);
    const centerX = width / 2;
    const centerY = height / 2;
    const scale = Math.min(width, height) / 980;

    const nodeById = new Map((graph?.nodes || []).map((node) => [node.id, node]));
    return {
        width,
        height,
        nodeById,
        points: (graph?.nodes || []).map((node) => ({
            id: node.id,
            label: node.label,
            entropy: node.entropy,
            degree: node.degree,
            x: centerX + (node.x * scale),
            y: centerY + (node.y * scale),
            radius: 2.8 + Math.min(5.5, node.degree * 0.3),
        })),
        edges: (graph?.edges || [])
            .map((edge) => {
                const source = nodeById.get(edge.source);
                const target = nodeById.get(edge.target);
                if (!source || !target) return null;
                return {
                    source: {
                        x: centerX + (source.x * scale),
                        y: centerY + (source.y * scale),
                    },
                    target: {
                        x: centerX + (target.x * scale),
                        y: centerY + (target.y * scale),
                    },
                };
            })
            .filter(Boolean),
    };
}

function renderCanvasFallback(graph) {
    const projection = computeProjection(graph);
    const context = canvas.getContext('2d');
    if (!context) return;

    canvas.width = projection.width;
    canvas.height = projection.height;
    context.clearRect(0, 0, projection.width, projection.height);
    context.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--abyss-bg') || '#181311';
    context.fillRect(0, 0, projection.width, projection.height);

    context.strokeStyle = 'rgba(130, 112, 86, 0.34)';
    context.lineWidth = 1;
    for (const edge of projection.edges) {
        context.beginPath();
        context.moveTo(edge.source.x, edge.source.y);
        context.lineTo(edge.target.x, edge.target.y);
        context.stroke();
    }

    for (const node of projection.points) {
        context.beginPath();
        context.fillStyle = entropyColor(node.entropy);
        context.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        context.fill();
    }

    projectedNodes = projection.points;
}

function renderGraph(graph) {
    latestGraph = graph;
    if (!graph || !Array.isArray(graph.nodes)) {
        return;
    }

    if (wasmRenderGraph) {
        try {
            wasmRenderGraph(JSON.stringify(graph));
            projectedNodes = computeProjection(graph).points;
            return;
        } catch (error) {
            console.warn('[abyss] wasm render failed; falling back to JS canvas', error);
            wasmRenderGraph = null;
            statRenderer.textContent = 'js-fallback';
        }
    }
    renderCanvasFallback(graph);
}

function nearestNode(clientX, clientY) {
    if (!projectedNodes.length) {
        return null;
    }
    const rect = canvas.getBoundingClientRect();
    const targetX = clientX - rect.left;
    const targetY = clientY - rect.top;

    let best = null;
    let bestDistance = Number.POSITIVE_INFINITY;
    for (const node of projectedNodes) {
        const dx = node.x - targetX;
        const dy = node.y - targetY;
        const distance = Math.sqrt((dx * dx) + (dy * dy));
        if (distance < bestDistance) {
            bestDistance = distance;
            best = node;
        }
    }
    if (!best || bestDistance > Math.max(10, best.radius + 5)) {
        return null;
    }
    return best;
}

async function bootstrapRenderer() {
    statRenderer.textContent = 'js-fallback';
    if (!boot.wasmModuleUri) {
        return;
    }

    try {
        const module = await import(boot.wasmModuleUri);
        if (typeof module.default === 'function') {
            await module.default(boot.wasmBinaryUri);
        }
        if (typeof module.init_renderer === 'function') {
            await module.init_renderer('graph-canvas');
        }
        if (typeof module.render_graph === 'function') {
            wasmRenderGraph = module.render_graph;
            statRenderer.textContent = 'rust-wasm';
            if (latestGraph) {
                renderGraph(latestGraph);
            }
        }
    } catch (error) {
        console.warn('[abyss] wasm bridge unavailable, keeping JS fallback', error);
        statRenderer.textContent = 'js-fallback';
    }
}

canvas.addEventListener('dblclick', (event) => {
    const node = nearestNode(event.clientX, event.clientY);
    if (!node) {
        return;
    }
    vscode.postMessage({ type: 'openFile', path: node.id });
});

window.addEventListener('resize', () => {
    if (latestGraph) {
        renderGraph(latestGraph);
    }
});

window.addEventListener('message', (event) => {
    const message = event.data;
    if (!message || !message.type) {
        return;
    }
    if (message.type === 'graph') {
        renderGraph(message.graph);
        return;
    }
    if (message.type === 'snapshot' && message.snapshot) {
        const snapshot = message.snapshot;
        statFiles.textContent = String(snapshot.totalFiles || 0);
        statEntropy.textContent = `${Math.round((snapshot.averageEntropy || 0) * 100)}%`;
    }
});

applyCircadianTheme();
setInterval(applyCircadianTheme, 60_000);
void bootstrapRenderer();
vscode.postMessage({ type: 'ready' });
