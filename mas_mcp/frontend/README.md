# 🧬 MAS-MCP Genesis Dashboard

Bun-native dashboard for monitoring the Meta-Archaeological Salvager Genesis Scheduler.

## Requirements

- **Bun v1.3.0+** (tested on v1.3.4)
- Windows 11 / Linux / macOS

## Quick Start

```bash
cd mas_mcp/frontend

# Install dependencies
bun install

# Run development server (with hot reload)
bun dev

# Run production server
bun start
```

Server runs at: **http://127.0.0.1:4000**

## Directory Structure

```
frontend/
├── api/              # API route handlers
│   └── routes.ts     # Digest, cycles, entities endpoints
├── lib/              # Shared libraries
│   ├── artifacts.ts  # File reading for Genesis artifacts
│   ├── config.ts     # Configuration & SLO thresholds
│   └── types.ts      # TypeScript definitions
├── public/           # Static assets
│   ├── index.html    # Dashboard HTML
│   ├── styles.css    # CSS (no preprocessor)
│   └── app.js        # Vanilla JS client
├── server.ts         # Bun.serve entry point
├── bunfig.toml       # Bun configuration
└── package.json
```

## API Endpoints

| Endpoint                | Method | Description                       |
|-------------------------|--------|-----------------------------------|
| `/api/health`           | GET    | Server health & version info      |
| `/api/digest`           | GET    | Today's daily digest              |
| `/api/digest/:date`     | GET    | Digest for specific date          |
| `/api/cycles`           | GET    | List cycle reports (paginated)    |
| `/api/cycles/:id`       | GET    | Single cycle by ID                |
| `/api/metrics`          | GET    | Aggregated 7-day metrics          |
| `/api/entities`         | GET    | All entities from registry        |
| `/api/entities/recent`  | GET    | Recently generated entities       |

## Configuration

Environment variables (`.env` file):

```env
# Server
PORT=8080
HOST=127.0.0.1

# MAS-MCP Paths (relative to frontend/)
GENESIS_LOGS_DIR=../logs/genesis
GENESIS_ARTIFACTS_DIR=../genesis_artifacts
ENTITY_REGISTRY_PATH=../data/entity_registry.json

# GPU Provider (display only)
GENESIS_GPU_PROVIDER=CUDA+TensorRT

# SLO Thresholds
SLO_ACCEPTANCE_RATE=0.35
SLO_P50_LATENCY_MS=50
SLO_P95_LATENCY_MS=200
SLO_VRAM_PCT=90
```

## Architecture Notes

This frontend is a **pure visualization layer**:

1. **No schema modification** – Reads artifacts as-is from backend
2. **No backend logic duplication** – Python GPU lane handles synthesis
3. **Macro-prompt-world compliance** – Respects `.github/copilot-instructions.md` as source of truth
4. **Zero external dependencies** – Uses only Bun built-ins

## Development

```bash
# Type checking
bun typecheck

# Hot reload server
bun --hot run server.ts
```

## License

MIT
