import * as fs from 'fs';
import * as path from 'path';

export type RustificationTier = 'gate' | 'lens' | 'loom';

export interface RustificationMarker {
    file: string;
    weight: number;
    present: boolean;
}

export interface RustificationReport {
    score: number;
    tier: RustificationTier;
    markers: RustificationMarker[];
    present: string[];
    missing: string[];
}

const MARKERS: Array<Omit<RustificationMarker, 'present'>> = [
    { file: 'uv.lock', weight: 25 },
    { file: 'Cargo.toml', weight: 22 },
    { file: 'mise.toml', weight: 18 },
    { file: '.mise.toml', weight: 8 },
    { file: '.ruby-version', weight: 10 },
    { file: 'go.mod', weight: 10 },
    { file: 'native/Cargo.toml', weight: 7 },
];

export async function computeRustificationReport(rootPath: string): Promise<RustificationReport> {
    const markers = MARKERS.map((marker) => {
        const fullPath = path.join(rootPath, marker.file);
        const present = fs.existsSync(fullPath);
        return {
            ...marker,
            present,
        };
    });

    const score = Math.min(
        100,
        markers.reduce((sum, marker) => (marker.present ? sum + marker.weight : sum), 0),
    );
    const tier = resolveTier(score);

    return {
        score,
        tier,
        markers,
        present: markers.filter((marker) => marker.present).map((marker) => marker.file),
        missing: markers.filter((marker) => !marker.present).map((marker) => marker.file),
    };
}

export function iconFileForTier(tier: RustificationTier): string {
    switch (tier) {
        case 'loom':
            return 'loom.svg';
        case 'lens':
            return 'lens.svg';
        default:
            return 'gate.svg';
    }
}

export function resolveTier(score: number): RustificationTier {
    if (score >= 80) {
        return 'loom';
    }
    if (score >= 45) {
        return 'lens';
    }
    return 'gate';
}
