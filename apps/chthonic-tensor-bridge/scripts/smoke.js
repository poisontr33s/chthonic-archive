#!/usr/bin/env node
'use strict';

// Smoke test for chthonic-tensor-bridge.
// Requires:
//   1. The native addon built (npm run build)
//   2. The flux-satellite daemon NOT yet running (the bridge spawns it)
//   3. A sealed engine + seal.json present at apps/flux-satellite/engines/
//   4. The same master_secret that was used to seal the engine

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const bridge = require('..');

async function main() {
    const prompt = process.argv[2] || 'a photograph of an astronaut riding a horse';

    // Master secret: read from FLUX_MASTER_SECRET env (set by the operator
    // after the forge run; in production this lives in VS Code SecretStorage).
    const secret = process.env.FLUX_MASTER_SECRET;
    if (!secret || secret.length < 32) {
        console.error('FATAL: FLUX_MASTER_SECRET env var missing or < 32 chars.');
        process.exit(2);
    }

    console.log('[smoke] hardware fingerprint:', bridge.hardwareFingerprint());
    bridge.setMasterSecret(secret);

    const repoRoot = path.resolve(__dirname, '..', '..', '..');
    const uvPath = process.env.UV_BIN || 'uv';
    const satelliteCwd = path.join(repoRoot, 'apps', 'flux-satellite');

    console.log('[smoke] spawning flux-satellite ...');
    await bridge.startSatellite({ uvPath, cwd: satelliteCwd });

    try {
        console.log('[smoke] health check ...');
        const health = await bridge.healthCheck();
        console.log('[smoke] health:', health);

        console.log('[smoke] generating:', JSON.stringify(prompt));
        const t0 = Date.now();
        const result = await bridge.generate({
            prompt,
            steps: 22,
            guidance: 3.5,
            width: 1024,
            height: 1024,
            seed: crypto.randomInt(0, 2 ** 31 - 1),
        });
        const wall = Date.now() - t0;
        console.log(`[smoke] gen_ms=${result.genMs} wall=${wall}ms dims=${result.width}x${result.height}`);

        const scratch = path.join(__dirname, '..', 'scratch');
        fs.mkdirSync(scratch, { recursive: true });
        const out = path.join(scratch, `smoke-${Date.now()}.rgba`);
        fs.writeFileSync(out, result.buffer);
        console.log('[smoke] wrote RGBA payload ->', out);
        console.log('[smoke] (convert via: ffmpeg -f rawvideo -pixel_format rgba ' +
                    `-video_size ${result.width}x${result.height} -i ${out} smoke.png)`);
    } finally {
        bridge.clearMasterSecret();
        await bridge.stopSatellite(true);
    }
}

main().catch((err) => {
    console.error('[smoke] FAILED:', err.code || '', err.message);
    bridge.clearMasterSecret();
    process.exit(1);
});
