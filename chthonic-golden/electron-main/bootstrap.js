// @ankh: inheritance — WEPET-ER boot protocol: cache clear, process fork, I/O unlock, thread isolation
// Chthonic Golden — Hardened Electron Bootstrap
// This module is injected before VS Code's main entry point.
// It applies GPU policy, V8 tuning, and crash recovery at the Electron level.

'use strict';

const { app } = require('electron');
const path = require('path');
const fs = require('fs');

// ---------------------------------------------------------------------------
// 1. LOAD GPU POLICY (gpu-policy.json — baked into distribution)
// ---------------------------------------------------------------------------

const GPU_POLICY_PATH = path.join(__dirname, 'gpu-policy.json');

let gpuPolicy;
try {
    const raw = fs.readFileSync(GPU_POLICY_PATH, 'utf8');
    gpuPolicy = JSON.parse(raw);
} catch {
    // @ankh: silence-semantics — if policy is missing, fail loud, not silent
    console.error('[CHTHONIC-GOLDEN] FATAL: gpu-policy.json not found or invalid at', GPU_POLICY_PATH);
    process.exit(1);
}

// ---------------------------------------------------------------------------
// 2. APPLY GPU FLAGS (before app ready — Chromium requires these early)
// ---------------------------------------------------------------------------

const gpu = gpuPolicy.gpu || {};

if (gpu.enableGpuRasterization) {
    app.commandLine.appendSwitch('enable-gpu-rasterization');
}

if (gpu.ignoreGpuBlocklist) {
    app.commandLine.appendSwitch('ignore-gpu-blocklist');
}

if (gpu.enableZeroCopy) {
    app.commandLine.appendSwitch('enable-zero-copy');
}

if (gpu.enableNativeGpuMemoryBuffers) {
    app.commandLine.appendSwitch('enable-native-gpu-memory-buffers');
}

if (gpu.useAngle && gpu.useAngle !== 'default') {
    app.commandLine.appendSwitch('use-angle', gpu.useAngle);
}

if (gpu.disableHardwareAcceleration) {
    app.disableHardwareAcceleration();
}

// ---------------------------------------------------------------------------
// 3. APPLY V8 HEAP TUNING
// ---------------------------------------------------------------------------

const v8Config = gpuPolicy.v8 || {};

if (v8Config.maxOldSpaceSize) {
    app.commandLine.appendSwitch('js-flags', `--max-old-space-size=${v8Config.maxOldSpaceSize}`);
}

// ---------------------------------------------------------------------------
// 4. CRASH RECOVERY WATCHDOG (SEKHMET → Hathor de-escalation)
// ---------------------------------------------------------------------------
// @ankh: constraint-philosophy — Sekhmet override + Red Beer fail-safe:
// After maxCrashRestartsPerHour, system de-escalates into safe mode (Hathor)

const crashConfig = gpuPolicy.crashRecovery || {};
const crashTimestamps = [];

function recordCrash() {
    const now = Date.now();
    crashTimestamps.push(now);

    // Prune timestamps older than 1 hour
    const oneHourAgo = now - 3600000;
    while (crashTimestamps.length > 0 && crashTimestamps[0] < oneHourAgo) {
        crashTimestamps.shift();
    }

    if (crashTimestamps.length >= (crashConfig.maxCrashRestartsPerHour || 3)) {
        console.warn('[CHTHONIC-GOLDEN] SEKHMET → HATHOR: too many crashes, entering safe mode');
        // Set environment variable for downstream consumers (extension host, etc.)
        process.env.CHTHONIC_SAFE_MODE = '1';
        return true; // safe mode triggered
    }
    return false;
}

// ---------------------------------------------------------------------------
// 5. STARTUP OPTIMIZATION (WEPET-ER protocol)
// ---------------------------------------------------------------------------

const startupConfig = gpuPolicy.startup || {};

if (startupConfig.preloadGpuProcess) {
    // Force GPU process spawn early — reduces first-paint latency
    app.commandLine.appendSwitch('in-process-gpu');
}

// ---------------------------------------------------------------------------
// 6. EXTENSION HOST MEMORY LIMITS
// ---------------------------------------------------------------------------

const processConfig = gpuPolicy.process || {};

if (processConfig.extensionHostMaxOldSpaceSize) {
    process.env.CHTHONIC_EXTHOST_MAX_OLD_SPACE = String(processConfig.extensionHostMaxOldSpaceSize);
}

if (processConfig.sharedProcessMaxOldSpaceSize) {
    process.env.CHTHONIC_SHARED_PROCESS_MAX_OLD_SPACE = String(processConfig.sharedProcessMaxOldSpaceSize);
}

// ---------------------------------------------------------------------------
// 7. EXPOSE BOOTSTRAP STATE
// ---------------------------------------------------------------------------

process.env.CHTHONIC_GOLDEN_BOOTSTRAP = '1';
process.env.CHTHONIC_GOLDEN_VERSION = require('../product.json').date || 'dev';

// Export for potential downstream use
module.exports = {
    gpuPolicy,
    recordCrash,
    isSafeMode: () => process.env.CHTHONIC_SAFE_MODE === '1'
};

// ---------------------------------------------------------------------------
// 8. LOG BOOTSTRAP COMPLETION
// ---------------------------------------------------------------------------

console.log('[CHTHONIC-GOLDEN] Bootstrap complete. GPU:', gpu.enableGpuRasterization ? 'HW' : 'SW',
    '| V8 heap:', v8Config.maxOldSpaceSize || 'default', 'MB',
    '| Crash watchdog:', crashConfig.enableWatchdog ? 'ON' : 'OFF');
