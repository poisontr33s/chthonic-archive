---
type: mailbox-report
created: 2026-03-08
subject: forge-dedup
---

# Forge Dedup Audit

## Furnace ↔ Tempered Comparison

Shared language lanes:

| Lane | Shared Files | Shared Identical | Furnace-only |
|---|---:|---:|---:|
| `c_cpp` | 1 | 1 | 0 |
| `csharp` | 2 | 2 | 24 |
| `docs` | 5 | 5 | 0 |
| `go` | 1 | 1 | 0 |
| `powershell` | 2 | 2 | 0 |
| `python` | 1 | 1 | 0 |
| `ruby` | 1 | 1 | 0 |
| `schemas` | 2 | 2 | 0 |
| `typescript` | 2 | 2 | 0 |
| `workflows` | 2 | 2 | 0 |

### Actual Dedup State

The previous “18/18 graduation” claim is almost true for source artifacts:

- all shared source-bearing files are byte-identical between `furnace/` and `tempered/`
- **except** `furnace/csharp/`, which still contains `bin/` and `obj/` build outputs that do not exist in `tempered/`

So the real state is:

- source duplication: effectively `1:1`
- build-artifact duplication: furnace-only C# residue still present

## Empty Stages

| Stage | Current Files | Assessment |
|---|---:|---|
| `intake` | 1 README | designed, currently bypassed |
| `quench` | 1 README | designed validation gate, currently bypassed |
| `slag` | 1 README | designed dormant archive, currently unused |
| `tea-vault` | 1 README | designed superposition lane, currently unused |

These stages are not broken. They are scaffolded but underused. The README corpus makes it clear the pipeline was designed for richer circulation than the current direct furnace→tempered success path.

## Health Assessment

- `tempered/` is functioning as the graduation shelf.
- `furnace/` is acting as both provenance store and staging shelf.
- The pipeline design remains structurally sound.
- The main hygiene problem is not conceptual confusion. It is C# build-output residue inside `furnace/`.

## Proposal

1. Keep `furnace/` until provenance retention policy is explicitly decided.
2. If the project wants true post-graduation dedup, archive or ignore the C# `bin/` and `obj/` residue.
3. Do not collapse empty stages yet; their readmes still define future circulation semantics.
