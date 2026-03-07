# Sister Ferrum Embalmer

- Generated: `2026-03-07T02:33:33Z`
- Session: `2026-03-07T02-33-33Z_claudine_trilemma`
- Dry run: `True`
- Copy sources: `False`
- Existing sources: `7` / `8`

## Sources

- [present] `canon_runtime` :: `C:\Users\erdno\chthonic-archive\scripts\chthonic.ps1`
  note: SSOT runtime engine
  sha256: `E0A8B579D02EAC63FEABB809A1EAF414C229666BC6BF00DD39EF18CB27F1D28B`
  signals: `contains_chthonic_script_ref, contains_claudine_wrapper, contains_legacy_markers, contains_canon_markers, contains_mcp_bridge`
- [present] `compat_facade` :: `C:\Users\erdno\chthonic-archive\scripts\claudine.ps1`
  note: Thin compatibility wrapper
  sha256: `8093D80ABA018EAC80501FE18E16EB9E378398A91AA3FD8C0AE5C31FFE84F0DC`
  signals: `contains_chthonic_script_ref, contains_claudine_wrapper`
- [present] `profile_ingress` :: `C:\Users\erdno\.config\powershell\profile.ps1`
  note: Active PowerShell ingress
  sha256: `EB49401C1935281A2880A9716367E0FB4475EE65BC2BF25A0018DE9635ACA666`
  signals: `contains_chthonic_script_ref, contains_claudine_wrapper, contains_legacy_markers, contains_canon_markers, contains_profile_ingress, contains_mcp_bridge`
- [missing] `profile_stub` :: `C:\Users\erdno\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`
  note: Profile stub loader
- [present] `legacy_residue` :: `C:\Users\erdno\PsychoNoir-Kontrapunkt\scripts\claudineENV.ps1`
  note: Historical residue from Local AI era
  sha256: `2ED300C9669FC8604618CDDD0C9260B3264AF86BD01F4ED9540A3AC253B74A44`
  signals: `contains_claudine_wrapper, contains_legacy_markers`
- [present] `context_anchor` :: `C:\Users\erdno\chthonic-archive\.github\copilot-instructions.archive.md`
  note: Frozen SSOT mythology anchor
  sha256: `C9C5DB850E2B7491B545DC3CB2720753A8F999FE9B0BDA5230BA4895F784610C`
  signals: `contains_claudine_wrapper, contains_mcp_bridge, contains_ferrum, contains_qmr, contains_knights, contains_schrodinger`
- [present] `context_anchor` :: `C:\Users\erdno\chthonic-archive\dumpster-dive\BLACKSMITH_MATRIARCH.md`
  note: Sister Ferrum Scoriae profile
  sha256: `D28F2749040B6CA8BD63C39984693F78434FF02EA5ABA98DA6C62EC99A3A0742`
  signals: `contains_ferrum, contains_qmr, contains_knights, contains_schrodinger`
- [present] `context_timeline` :: `C:\Users\erdno\chthonic-archive\dumpster-dive\from-github\SR_SCHRODINGERS_BASTARD.md`
  note: Sir Schroedinger's Bastard linkage
  sha256: `129D629A2BE8C46D842F2E26B7DE929765F44EC496A104F2ED72775DD90D45BA`
  signals: `contains_ferrum, contains_qmr, contains_knights, contains_schrodinger`

## Interpretation

- canon_runtime and compat_facade are the live runtime surfaces.
- profile_ingress and profile_stub are the active ingress chain.
- legacy_residue is archaeology only unless a user deliberately revives it.
- context_anchor and context_timeline provide mythic alignment for Sister Ferrum / QMR / timeline residue.

## Next Actions

- Canonize naming and markers around CHTHONIC_*.
- Treat claudineENV.ps1 as residue, not runtime.
- Use this embalmer report before any future claudine/chthonic upcycle pass.
