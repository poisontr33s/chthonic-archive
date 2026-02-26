# Branding — Chthonic Golden

Placeholder directory for distribution branding assets.

## Required Assets

| File | Format | Size | Purpose |
|------|--------|------|---------|
| `icon.ico` | ICO | 256x256 multi-res | Windows application icon |
| `icon.png` | PNG | 512x512 | macOS/Linux application icon, README |
| `splash.svg` | SVG | viewport | Startup splash (optional) |

## Design Direction

- Primary color: **Gold (#FFD700)** — the ANKH color
- Background: **Deep black (#0D0D0D)** — chthonic earth
- Motif: **Mandala** — existing from `extensions/chthonic-archive/icons/mandala.png`
- Typography: **Monospace** — engineering identity

## Generation

Use the `imagegen` skill or:

```powershell
python scripts/image_gen.py --prompt "Golden ankh mandala icon, dark background, geometric, minimal" --size 512x512 --output chthonic-golden/branding/icon.png
```

> @ankh: mythic-identity — The golden mandala icon carries the fork's archetypal identity.
> It must be visually distinct from VS Code's blue icon while preserving the mandala lineage.
