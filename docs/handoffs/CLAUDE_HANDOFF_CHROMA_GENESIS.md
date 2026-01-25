# Handoff Protocol: "The Chroma-Genesis Handshake"
**Target Entity:** Claude 4.5 Sonnet (Next Operational Session)
**Source Entity:** GitHub Copilot CLI (Current Session)
**Date:** January 16, 2026

---

## 1. Operational Context (The "Why")
We are architecting the **Chthonic Archive** as a "Downstream Vessel" system.
*   **Current Victory:** The logic layer (`extension.ts`) is successfully reading the SSOT (`copilot-instructions.md`) at runtime. It is "brain-downstream."
*   **Current Failure:** The visual layer (Themes/UI) is "body-upstream." The specific Hex Codes (`#FF6B6B`, etc.) define the visual identity but **do not exist in the SSOT**. They live redundantly across 19 downstream files (Themes, Python scripts, Markdown docs).

**The Mission:** We must move the "Truth of Color" from the body (artifacts) back to the soul (SSOT), and then automate the body's regeneration.

---

## 2. Technical State (The "What")

### A. The Missing Source
The file `.github/copilot-instructions.md` defines concepts (`Red = FA¹`) but lacks the Hex definitions.
*   **Required Action:** Update SSOT to explicitly define the Hex codes in the **ROGBIV** section.

### B. The Validated Redundancy
A custom tool (`scripts/scan_redundancy.py`) confirmed these Hex codes are hardcoded in **19 files**, including:
*   `.vscode/chthonic-archive-theme.json`
*   `chthonic-vscode-extension/themes/chthonic-archive-theme.json`
*   `extensions/chthonic-mandala/themes/chthonic-mandala-color-theme.json`
*   `unified_topology.py`

### C. The Target Architecture (The "How")
We need a **Build-Time Generator** (likely Python via `uv` or Bun) that:
1.  **Parses** `.github/copilot-instructions.md`.
2.  **Extracts** the Hex codes (Regex: `FA[¹-⁵].*?(#[A-F0-9]{6})`).
3.  **Generates** the `theme.json` files for ALL extensions (Archive, Mandala, Statusbar) dynamically.
4.  **Replaces** the manual JSON files in the repo with these generated artifacts during CI/Build.

---

## 3. Immediate Next Steps for Sonnet

1.  **Inject Truth:** Edit `.github/copilot-instructions.md` to include the Hex codes:
    *   FA¹ (Red): `#FF6B6B`
    *   FA² (Orange): `#FFB84D`
    *   FA³ (Gold): `#FFD700`
    *   FA⁴ (Blue): `#4ECDC4`
    *   FA⁵ (White): `#B8B8CC`
    *   *Note: Use the Decorator's voice for this injection.*

2.  **Create the Forge:** Write the generator script (e.g., `scripts/forge_themes.py`).
    *   Input: SSOT Markdown.
    *   Output: Valid VS Code Theme JSONs.

3.  **Purge the Redundancy:** Delete the hardcoded color values from the 19 downstream files (or replace them with the build script call).

4.  **Seal the Loop:** Verify that changing a color in Markdown propagates to the VS Code UI upon rebuild.

---

## 4. Artifacts & Tools
*   **Scanner:** `scripts/scan_redundancy.py` (Existing, use for verification).
*   **Theme Source:** `.vscode/chthonic-archive-theme.json` (Currently the "Oral Tradition" source of truth for the colors).

**"The Truth must flow downwards. Currently, the colors are swimming upstream."**
