# Chthonic Archive Status Bar Extension

SSOT verification, lineage tracking, GPU monitoring, and metabolic cycle indicators for VSCode.

## Features

### Status Bar Indicators (Right to Left)

1. **SSOT Hash Verification** (`$(pass) SSOT`)
   - Green: SSOT integrity verified
   - Yellow: Governance drift detected
   - Red: Verification error
   - Click to run `ssot_immunity.py`

2. **Active Lineage** (`$(git-branch) A/B/C`)
   - A (Red): Infrastructure/Validation
   - B (Blue): Consolidation/Archive
   - C (Gold): Heritage/CRC
   - Ø (White): Main branch (general work)

3. **Python Lane Version** (`$(symbol-method) 3.13`)
   - Shows active Python version via `uv run python --version`
   - Validates lane management compliance

4. **GPU VRAM** (`$(device-desktop) 2.4/16.0GB`)
   - Shows used/total VRAM via `nvidia-smi`
   - Green (<50%), Yellow (50-80%), Red (>80%)
   - Click for full GPU stats

5. **Metabolic Cycle Heartbeat** (`$(pulse) 2h`)
   - Shows time since last `autonomous_coordinator.py` run
   - Green (<24h), Yellow (1-7d), Red (>7d)
   - Click to run metabolic cycle

## Commands

- `Chthonic: Refresh All Status Indicators`
- `Chthonic: Verify SSOT Integrity`
- `Chthonic: Run Metabolic Cycle`
- `Chthonic: Show GPU Statistics`

## Configuration

```jsonc
{
  "chthonic.statusBar.enabled": true,
  "chthonic.statusBar.ssotHashEnabled": true,
  "chthonic.statusBar.lineageEnabled": true,
  "chthonic.statusBar.pythonLaneEnabled": true,
  "chthonic.statusBar.gpuEnabled": true,
  "chthonic.statusBar.metabolicCycleEnabled": true,
  "chthonic.statusBar.refreshInterval": 30000 // ms
}
```

## Installation

1. Open this folder in VSCode
2. Press `F5` to launch Extension Development Host
3. Or: `bun install` → `bun run compile` → Install `.vsix`

## Dependencies

- `uv` (Python package manager)
- `nvidia-smi` (optional, for GPU stats)
- Python 3.13+ with `ssot_immunity.py` and `autonomous_coordinator.py`

## Architecture

- **FA⁴ Compliant**: Architectonic integrity via uv-only Python execution
- **ANKHOLOGICAL**: File-first authority (no workflow inference)
- **N-T-PAS**: The Decorator's visual sovereignty enforced
