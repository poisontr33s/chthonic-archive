# CODEKILLER Cross-Reference Audit

Generated: 2026-02-24
Scope: `anti-patterns/codekiller.md` frontmatter + in-body local evidence links

| Reference | Exists | Line Content (if found) | Status |
|---|---|---|---|
| `.github/copilot-instructions.md:44` | Yes | `Default Axiom (Wet-Paper-to-Gold): Every file is gold...` | PASS |
| `.github/copilot-instructions.archive.md:5670` | Yes (line exists) | `[blank line]` | FAIL (`line-content drift`; referenced statement not at this line) |
| `.github/copilot-instructions.archive.md:5676` | Yes | `→ TIER: ΔEXIST` | WARN (`line-content drift`; quoted governance statement appears at line 5675) |
| `WET_PAPER_TO_GOLD_METHODOLOGY.md:42` | Yes | `Every file is gold...` | PASS |
| `WET_PAPER_TO_GOLD_METHODOLOGY.md:68` | Yes | `No agent ... may destroy, displace, or disappear ANY file...` | PASS |
| `chthonic-archive_transmutation_framework_original.html` (evidence link) | Yes | Resolved path: `WET_PAPER_TO_GOLD_WIP/chthonic-archive_transmutation_framework_original.html` | PASS |
| `readme.md (in this folder-DIR-structure)` (policy_basis entry) | Ambiguous | Could mean `anti-patterns/README.md` (exists), but does not match the in-body link target | WARN (ambiguous reference target) |
| `file:///C:/Users/erdno/chthonic-archive/anti-patterns/codekiller/Readme.md` (in-body link at `anti-patterns/codekiller.md:46`) | No | Resolved path: `anti-patterns/codekiller/Readme.md` | FAIL (broken local link) |

## Notes

- `anti-patterns/codekiller.md` references narrative text tied to `.github/copilot-instructions.archive.md:5670` and `:5676`, but those exact lines no longer contain the quoted sentences.
- Closest active anchor for "governance substrate annihilation" is `.github/copilot-instructions.archive.md:5675`.
- The broken `anti-patterns/codekiller/Readme.md` link is consistent with remediation-gate blocker output (`broken_local_link_count = 1`).

## Verdict

- References checked: 8
- PASS: 4
- WARN: 2
- FAIL: 2
