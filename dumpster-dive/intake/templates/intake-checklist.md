---
refs:
  - manifest-template.yml
  - lineage-A-template/main.md
  - lineage-B-template/main.md
  - lineage-C-template/main.md
---

# Lineage Submission Checklist

## Coordination Rule (Applies to All Lineages)

When a status or instruction artifact states:
**"Awaiting sovereign population (Lineage X)"**

We interpret this as:
→ **Lineage X must populate its own `lineage-X-template/manifest.yml` and `main.md` immediately.**

No other lineage performs this action on its behalf.
This is an instruction, not a waiting state.

---

## Pre-Submission

- [ ] Lineage bundle named: `lineage-<A|B|C>-<shortname>.zip` or `.7z`
- [ ] `manifest.yml` present at bundle root
- [ ] All required manifest fields completed
- [ ] Phase marker (`🌀` or `⚓`) specified
- [ ] Entry point file path verified
- [ ] No SSOT files included (read-only references permitted)

## Optional

- [ ] Fresh `ankh_index.json` included (if regenerated locally)
- [ ] Diff snapshots included (if tracking changes)
- [ ] Notes field populated with context

## Submission

1. Upload bundle to session context
2. Wait for deterministic report (JSON + summary)
3. Review findings (Critical/High/Medium/Low)
4. Apply suggested fixes manually (if any)
5. Human approval required for any SSOT modifications

## Safety Boundaries

- No automatic changes will be made
- No code execution on submitter machine
- No external storage provisioning
- Large files flagged for safer transfer method
