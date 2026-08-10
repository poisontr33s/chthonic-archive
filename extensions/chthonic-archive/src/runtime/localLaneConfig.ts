// @SID: EXT_RUNTIME_LOCAL_LANE_CONFIG_V1
import * as fs from 'fs';
import * as path from 'path';

type Warn = (message: string) => void;

export interface LocalLaneConfigOptions {
    readonly extensionRoot: string;
    readonly workspaceRoot: string | null;
    readonly warn?: Warn;
}

export class LocalLaneConfig {
    constructor(
        readonly sourcePath: string | null,
        private readonly fileEnv: ReadonlyMap<string, string>,
        private readonly warn?: Warn,
    ) {}

    getString(name: string, fallback: string): string {
        const raw = this.raw(name);
        return raw === undefined ? fallback : raw.trim();
    }

    getBoolean(name: string, fallback: boolean): boolean {
        const raw = this.raw(name);
        if (raw === undefined) return fallback;
        const normalized = raw.trim().toLowerCase();
        if (['1', 'true', 'yes', 'on'].includes(normalized)) return true;
        if (['0', 'false', 'no', 'off'].includes(normalized)) return false;
        this.warn?.(`${name}=${raw} is not boolean; using fallback ${fallback}`);
        return fallback;
    }

    getNumber(name: string, fallback: number): number {
        const raw = this.raw(name);
        if (raw === undefined) return fallback;
        const parsed = Number(raw.trim());
        if (Number.isFinite(parsed)) return parsed;
        this.warn?.(`${name}=${raw} is not numeric; using fallback ${fallback}`);
        return fallback;
    }

    getEnum<T extends string>(name: string, allowed: readonly T[], fallback: T): T {
        const raw = this.raw(name);
        if (raw === undefined) return fallback;
        const trimmed = raw.trim();
        const match = allowed.find((value) => value === trimmed);
        if (match) return match;
        this.warn?.(`${name}=${raw} is not one of ${allowed.join(', ')}; using fallback ${fallback}`);
        return fallback;
    }

    private raw(name: string): string | undefined {
        const envValue = process.env[name];
        if (typeof envValue === 'string') return envValue;
        return this.fileEnv.get(name);
    }
}

export function loadLocalLaneConfig(options: LocalLaneConfigOptions): LocalLaneConfig {
    const sourcePath = findMiseToml(options.extensionRoot, options.workspaceRoot);
    if (!sourcePath) {
        return new LocalLaneConfig(null, new Map(), options.warn);
    }

    try {
        return new LocalLaneConfig(sourcePath, readMiseEnv(sourcePath, options.warn), options.warn);
    } catch (error) {
        options.warn?.(`failed to read ${sourcePath}: ${String(error)}`);
        return new LocalLaneConfig(null, new Map(), options.warn);
    }
}

function findMiseToml(extensionRoot: string, workspaceRoot: string | null): string | null {
    const candidates = [
        path.join(extensionRoot, '.chthonic', 'mise.toml'),
        workspaceRoot ? path.join(workspaceRoot, 'extensions', 'chthonic-archive', '.chthonic', 'mise.toml') : null,
    ];
    const seen = new Set<string>();
    for (const candidate of candidates) {
        if (!candidate) continue;
        const normalized = path.normalize(candidate);
        if (seen.has(normalized)) continue;
        seen.add(normalized);
        if (fs.existsSync(normalized)) return normalized;
    }
    return null;
}

function readMiseEnv(filePath: string, warn?: Warn): Map<string, string> {
    const values = new Map<string, string>();
    let inEnv = false;
    for (const line of fs.readFileSync(filePath, 'utf8').split(/\r?\n/)) {
        const trimmed = line.trim();
        if (trimmed.length === 0 || trimmed.startsWith('#')) continue;

        const table = /^\[([^\]]+)\]$/.exec(trimmed);
        if (table) {
            inEnv = table[1] === 'env';
            continue;
        }
        if (!inEnv) continue;

        const separator = trimmed.indexOf('=');
        if (separator < 1) continue;
        const key = trimmed.slice(0, separator).trim();
        if (!/^[A-Z0-9_]+$/.test(key)) continue;

        const scalar = parseScalar(stripInlineComment(trimmed.slice(separator + 1)).trim(), warn);
        if (scalar !== null) values.set(key, scalar);
    }
    return values;
}

function stripInlineComment(value: string): string {
    let quote: '"' | "'" | null = null;
    let escaped = false;
    for (let i = 0; i < value.length; i += 1) {
        const char = value[i];
        if (escaped) {
            escaped = false;
            continue;
        }
        if (quote === '"') {
            if (char === '\\') escaped = true;
            else if (char === '"') quote = null;
            continue;
        }
        if (quote === "'") {
            if (char === "'") quote = null;
            continue;
        }
        if (char === '"' || char === "'") {
            quote = char;
            continue;
        }
        if (char === '#') return value.slice(0, i);
    }
    return value;
}

function parseScalar(value: string, warn?: Warn): string | null {
    if (value.startsWith('"') && value.endsWith('"')) {
        try {
            return JSON.parse(value) as string;
        } catch {
            warn?.(`invalid quoted value ${value}`);
            return null;
        }
    }
    if (value.startsWith("'") && value.endsWith("'")) {
        return value.slice(1, -1);
    }
    return value;
}
