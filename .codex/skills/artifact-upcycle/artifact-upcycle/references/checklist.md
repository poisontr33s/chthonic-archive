---
type: reference
category: skill
skill: artifact-upcycle
description: Step-by-step checklist for artifact upcycling workflow
---

# Artifact-Upcycle Checklist

1. Confirm the target scope (file or directory group).
2. Identify file types and intent.
3. Choose the first applicable action:
   - Rename/relocate to canonical location
   - Add/repair cross-reference links
   - Add YAML frontmatter
   - Summarize into a clean artifact
   - Extract TODOs into a structured TODO.md (if present)
   - Apply script-envelope standardization (if script file)
   - Archive stale content
4. Apply minimal safe change.
5. Report updated path + brief diff summary.
6. Log the action to `codex/NEXT.md` if present.
