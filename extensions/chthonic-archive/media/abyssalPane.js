const vscode = acquireVsCodeApi();
const boot = window.__CHTHONIC_ABYSSAL__ || {};

const canvas = /** @type {HTMLCanvasElement} */ (document.getElementById('graph-canvas'));
const statFiles = document.getElementById('stat-files');
const statEntropy = document.getElementById('stat-entropy');
const statRenderer = document.getElementById('stat-renderer');

let wasmRenderGraph = null;
let latestGraph = null;
let latestSediment = null;
let sedimentStreamBuffer = [];
let sedimentStreamMeta = null;
let projectedNodes = [];
let sedimentMode = false;

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

// ---------------------------------------------------------------------------
// Sediment renderer — 3D particle field projected to Canvas 2D
// ---------------------------------------------------------------------------

function renderSediment(sediment) {
    latestSediment = sediment;
    sedimentMode = true;
    const vertices = sediment?.vertices;
    if (!vertices || !vertices.length) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = Math.max(320, canvas.clientWidth);
    const h = Math.max(220, canvas.clientHeight);
    canvas.width = w;
    canvas.height = h;

    // Void background
    const bg = getComputedStyle(document.documentElement).getPropertyValue('--abyss-bg') || '#0a0908';
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, w, h);

    // Perspective projection parameters
    const fov = 600;          // focal length (pixels)
    const camY = -30;         // camera lifted above the field
    const camZ = -80;         // camera pulled back
    const cx = w / 2;
    const cy = h / 2;

    // Project each vertex to screen space, store for z-sort
    const projected = vertices.map((v) => {
        // Camera-relative position
        const rz = v.z - camZ;
        const ry = v.y - camY;
        const depth = Math.max(rz, 1); // prevent division by zero
        const scale = fov / depth;

        return {
            sx: cx + v.x * scale,
            sy: cy + ry * scale,
            sr: Math.max(1, v.radius * scale * 0.5),
            r: v.r,
            g: v.g,
            b: v.b,
            alpha: v.alpha,
            depth,
        };
    });

    // Z-sort: farthest first (painter's algorithm)
    projected.sort((a, b) => b.depth - a.depth);

    // Draw particles
    for (const p of projected) {
        const r = Math.round(clamp01(p.r) * 255);
        const g = Math.round(clamp01(p.g) * 255);
        const b = Math.round(clamp01(p.b) * 255);
        const a = clamp01(p.alpha);

        // Depth-fade: distant particles become more transparent
        const depthFade = clamp01(1 - (p.depth - 1) / 300);
        const finalAlpha = a * depthFade;

        if (finalAlpha < 0.01 || p.sx < -50 || p.sx > w + 50 || p.sy < -50 || p.sy > h + 50) {
            continue; // cull offscreen / invisible
        }

        // Glow halo for bright particles
        if (finalAlpha > 0.4 && p.sr > 2) {
            const grad = ctx.createRadialGradient(p.sx, p.sy, p.sr * 0.3, p.sx, p.sy, p.sr * 2.5);
            grad.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${finalAlpha * 0.3})`);
            grad.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);
            ctx.fillStyle = grad;
            ctx.fillRect(p.sx - p.sr * 2.5, p.sy - p.sr * 2.5, p.sr * 5, p.sr * 5);
        }

        // Core particle
        ctx.beginPath();
        ctx.arc(p.sx, p.sy, p.sr, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${finalAlpha})`;
        ctx.fill();
    }

    // Update stats
    statFiles.textContent = String(sediment.file_count || vertices.length);
    statEntropy.textContent = sediment.backend || 'cpu';
    statRenderer.textContent = `${sediment.compute_time_ms || '?'}ms`;

    // Store projected nodes for click interaction
    projectedNodes = projected.map((p) => ({
        x: p.sx,
        y: p.sy,
        radius: p.sr,
        id: null,
        label: null,
        entropy: 0,
        degree: 0,
    }));
}

function applySedimentChunk(chunk) {
    if (!chunk || !Array.isArray(chunk.vertices)) {
        return;
    }

    if (!sedimentStreamMeta || chunk.chunk_index === 0) {
        sedimentStreamBuffer = [];
        sedimentStreamMeta = {
            total_chunks: chunk.total_chunks || 1,
            layer_count: chunk.layer_count || 0,
            file_count: chunk.file_count || 0,
            backend: chunk.backend || 'stream',
        };
    }

    sedimentStreamBuffer.push(...chunk.vertices);
    renderSediment({
        vertices: sedimentStreamBuffer,
        layer_count: sedimentStreamMeta.layer_count,
        file_count: sedimentStreamMeta.file_count,
        compute_time_ms: chunk.chunk_index + 1,
        backend: `${sedimentStreamMeta.backend} stream ${(chunk.chunk_index + 1)}/${sedimentStreamMeta.total_chunks}`,
    });
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
    if (sedimentMode && latestSediment) {
        renderSediment(latestSediment);
    } else if (latestGraph) {
        renderGraph(latestGraph);
    }
});

window.addEventListener('message', (event) => {
    const message = event.data;
    if (!message || !message.type) {
        return;
    }
    if (message.type === 'sediment' && message.sediment) {
        sedimentStreamBuffer = [];
        sedimentStreamMeta = null;
        renderSediment(message.sediment);
        return;
    }
    if (message.type === 'sedimentChunk' && message.chunk) {
        applySedimentChunk(message.chunk);
        return;
    }
    if (message.type === 'graph') {
        sedimentMode = false;
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
vscode.postMessage({ type: 'requestSediment' });
