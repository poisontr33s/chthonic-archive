# renders/

Renderer frame captures from `scripts/render-smoke.ps1` (the `CHTHONIC_SCREENSHOT`
framebuffer→PNG dump). Lives at the repo root so it shows in the VS Code explorer —
unlike `target/`, which `files.exclude` hides.

This is a plain, fully-tracked folder: the README, `.gitkeep`, and the PNG captures
are all committed. No `.gitignore` rule touches `renders/`, so it shows up in the
workspace as an ordinary folder — not a separate/ignored satellite.

Current capture: `render-smoke.png` (overwritten each smoke run; the commit just
carries the latest frame).
