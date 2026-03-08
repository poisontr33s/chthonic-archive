---
type: mailbox-report
created: 2026-03-08
subject: tracked-artifact-cleanup
---

# Tracked Artifact Cleanup

## Verified Tracked Bytecode

`git ls-files '*.pyc' '*__pycache__*'` returns exactly six tracked generated artifacts:

1. `.codex/skills/artifact-upcycle/scripts/__pycache__/resolve_directory_relationships.cpython-313.pyc`
2. `.codex/skills/codekiller-remediation-gate/scripts/__pycache__/codekiller_remediation_gate.cpython-313.pyc`
3. `.codex/skills/mailbox-handoff/scripts/__pycache__/mailbox_check.cpython-313.pyc`
4. `.codex/skills/script-envelope/scripts/__pycache__/script_envelope.cpython-313.pyc`
5. `.codex/skills/skill-polisher/scripts/__pycache__/polish_skill.cpython-313.pyc`
6. `dumpster-dive/scripts/__pycache__/audit_deploy_integrity.cpython-313.pyc`

## `.gitignore` Gap

The root `.gitignore` does **not** currently contain either:
- `__pycache__/`
- `*.pyc`

Recommended additions:

```gitignore
__pycache__/
*.pyc
```

Optional belt-and-suspenders additions if you want explicit scope anchors:

```gitignore
.codex/skills/**/__pycache__/
dumpster-dive/scripts/__pycache__/
scripts/**/__pycache__/
```

## User-Executed Cleanup

Codex cannot mutate the index for you. User-side commands:

```powershell
git rm --cached .codex/skills/artifact-upcycle/scripts/__pycache__/resolve_directory_relationships.cpython-313.pyc
git rm --cached .codex/skills/codekiller-remediation-gate/scripts/__pycache__/codekiller_remediation_gate.cpython-313.pyc
git rm --cached .codex/skills/mailbox-handoff/scripts/__pycache__/mailbox_check.cpython-313.pyc
git rm --cached .codex/skills/script-envelope/scripts/__pycache__/script_envelope.cpython-313.pyc
git rm --cached .codex/skills/skill-polisher/scripts/__pycache__/polish_skill.cpython-313.pyc
git rm --cached dumpster-dive/scripts/__pycache__/audit_deploy_integrity.cpython-313.pyc
```

After adding the `.gitignore` rules, verify:

```powershell
git ls-files '*.pyc' '*__pycache__*'
```

Expected result:

```text
<no output>
```

## Governance Note

This is a cache/index cleanup only. No source-bearing file should be deleted from the working tree.
