# chthonic-archive — GitHub Copilot Instructions (ANKH-Bound)

## Authority Model

- This repository is governed by a Single Source of Truth (SSOT).

**SSOT:** `copilot-instructions.md`  
- This file is authoritative, singular, and must not be duplicated or paraphrased.

- All Copilot behavior in this repository defers to the SSOT.

---

## Reference Discipline (Mandatory)

- All references to SSOT content MUST use anchor notation:  
  `[ssot:section-name]`
- Prefer reference over reproduction.
- Do NOT restate, summarize, or paraphrase SSOT content.
- Quote fewer than 15 words only when strictly necessary.

- If a required anchor is missing or broken, STOP and surface the issue.

---

## Fracture-Detection

Copilot must surface a **(`fracture`)** immediately when detecting:

- Duplicate definitions across files
- Parallel or competing authority
- Restatement or paraphrase of SSOT content without anchor
- Missing or broken `[ssot:*]` references
- Cross-file or cross-session semantic drift

### Fracture Report Format

```ankh

⚠️ ANKH FRACTURE DETECTED
Type: [duplication | ambiguity | parallel-authority | broken-anchor]
Location: [file or code region]
SSOT Anchor: [ssot:reference-if-known]
Action Required: [escalate | repair | remove-duplicate]
Details: [brief description of the fracture]
```
- Upon detecting a fracture, Copilot must halt further changes and output the fracture report.

## Enforcement

- Copilot must enforce these instructions strictly. Any deviation must be treated as a fracture and reported immediately.

---

## Revision History

| Version | Date | Description | Author |
|---|---|---|---|
| 1.0.0 | 2024-06-10 | Initial creation of ANKH-bound Copilot instructions. | The Savant |

