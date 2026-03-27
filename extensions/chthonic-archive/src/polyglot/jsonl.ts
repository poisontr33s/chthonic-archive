// @SID: EXT_JSONL_V1
export interface JsonlDecoder {
    push(chunk: string | Buffer): void;
    flush(): void;
}

export function createJsonlDecoder(
    onMessage: (value: Record<string, unknown>) => void,
    onError: (error: Error) => void,
): JsonlDecoder {
    let buffer = '';

    const processLine = (line: string): void => {
        const trimmed = line.trim();
        if (!trimmed) {
            return;
        }
        try {
            const parsed = JSON.parse(trimmed);
            if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
                throw new Error('JSONL payload must be an object');
            }
            onMessage(parsed as Record<string, unknown>);
        } catch (error) {
            onError(error instanceof Error ? error : new Error(String(error)));
        }
    };

    return {
        push(chunk: string | Buffer): void {
            buffer += chunk.toString();
            while (true) {
                const newlineIndex = buffer.indexOf('\n');
                if (newlineIndex < 0) {
                    return;
                }
                const line = buffer.slice(0, newlineIndex);
                buffer = buffer.slice(newlineIndex + 1);
                processLine(line);
            }
        },
        flush(): void {
            if (!buffer.trim()) {
                buffer = '';
                return;
            }
            processLine(buffer);
            buffer = '';
        },
    };
}
