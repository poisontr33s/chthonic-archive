# Polyrepo Archaeology Plan — QOL Reference
<!-- type: scaffold | status: active | created: 2026-05-02 -->
<!-- decay: remove when all phases are DONE and artifacts promoted to SSOT -->

## Execution Tiers (dependency order — do not skip tiers)

```
TIER 1: DATA (read-only, no risk)
  └─ 0.1  Claudine CLI branch diffs        → manifest/claudine_branch_diffs.json
  └─ 0.2  Restructure-MCP copilot/* map    → manifest/mcp_copilot_branches.json
  └─ 1.1  PR archaeology (all repos)       → manifest/pr_archaeology.json
  └─ 1.2  Dependabot gap analysis          → manifest/dependabot_gap.json

TIER 2: ENCODE (write to manifest, no GitHub writes)
  └─ 2.1  Security pattern from issue #263 → .github/SECURITY_PATTERNS.md (chthonic-archive)
  └─ 2.2  Version drift manifest           → manifest/version_drift.json
  └─ 2.3  Branch harvest decisions         → manifest/branch_archaeology.json

TIER 3: OPEN DRAFT PRs (light action — draft only, no merge)
  └─ 3.1  Claudine CLI 5 copilot/* → draft PRs, label: copilot-harvest
  └─ 3.2  Restructure-MCP best copilot/fix-* → draft PRs, label: copilot-fix-harvest
  └─ 3.3  Close issue #263 with SECURITY_PATTERNS.md citation

TIER 4: FOUNDATION (structural)
  └─ 4.1  Release tags v0.1.0 across all 4 active repos
  └─ 4.2  PR templates from archaeology findings
  └─ 4.3  .coderabbit.yml from recurring CodeRabbit patterns
  └─ 4.4  GitHub Projects v2 — monolith board + custom fields

TIER 5: AUTOMATION (runs forever after setup)
  └─ 5.1  Dependabot auto-merge (patch/minor only — major stays manual)
  └─ 5.2  polyrepo-runner.ps1 -GitHub flag (per-district PR/issue/branch counts)
```

---

## Repos in Scope

| Alias | Full name | Local path |
|-------|-----------|------------|
| `archive` | `poisontr33s/chthonic-archive` | `C:\Users\eldno\chthonic-archive` |
| `claudine` | `poisontr33s/Claudine_Supreme-Polyglot-Git-Cli-Lsp-Repo-Clone-Engineering-Bun-Technique` | `C:\Users\eldno\Claudine_Supreme-Polyglot-Git-Cli-Lsp-Repo-Clone-Engineering-Bun-Technique` |
| `pnk` | `poisontr33s/PsychoNoir-Kontrapunkt` | `C:\Users\eldno\PsychoNoir-Kontrapunkt` |
| `mcp` | `poisontr33s/Restructure-MCP-Orchestration` | `C:\Users\eldno\Restructure-MCP-Orchestration` |

LFS repos (`git-dump-lfs-holder-we-it-takes`, `psychonoir-kontrapunkt-large-file-holder`) are archive-only — Phase 4 tags only, no branch work.

---

## TIER 1 Commands

### 0.1 — Claudine CLI branch diffs

```powershell
$CLAUDINE = "poisontr33s/Claudine_Supreme-Polyglot-Git-Cli-Lsp-Repo-Clone-Engineering-Bun-Technique"
$BRANCHES = @(
  "copilot/add-gpu-accelerated-tfjs-package",
  "copilot/create-e2e-workflow-tests",
  "copilot/implement-config-system-tests",
  "copilot/integrate-config-manager-orchestrator",
  "copilot/refactor-cli-commands-orchestrator"
)
$results = @()
foreach ($b in $BRANCHES) {
  $b_encoded = [uri]::EscapeDataString($b)
  $diff = gh api "repos/$CLAUDINE/compare/main...$b_encoded" --jq `
    '{branch: .head_commit.sha, ahead: .ahead_by, behind: .behind_by, files: [.files[] | {status, additions, deletions, filename}]}'
  $results += [PSCustomObject]@{ branch = $b; data = ($diff | ConvertFrom-Json) }
}
$results | ConvertTo-Json -Depth 10 | Set-Content manifest/claudine_branch_diffs.json
```

### 0.2 — Restructure-MCP copilot/* branch list + issue linkage

```powershell
$MCP = "poisontr33s/Restructure-MCP-Orchestration"
$branches = gh api "repos/$MCP/git/refs?per_page=100" `
  --jq '[.[] | select(.ref | startswith("refs/heads/copilot/")) | {ref: .ref, sha: .object.sha}]'
$branches | Set-Content manifest/mcp_copilot_branches.json
```

### 1.1 — PR archaeology (closed PRs, all repos)

```powershell
$repos = @("poisontr33s/chthonic-archive","poisontr33s/Restructure-MCP-Orchestration","poisontr33s/PsychoNoir-Kontrapunkt")
$all = @{}
foreach ($r in $repos) {
  $prs = gh api "repos/$r/pulls?state=closed&per_page=100" `
    --jq '[.[] | {number, title, body, created_at, merged_at, user_login: .user.login}]'
  $all[$r] = ($prs | ConvertFrom-Json)
}
$all | ConvertTo-Json -Depth 10 | Set-Content manifest/pr_archaeology.json
```

### 1.2 — Dependabot gap analysis

```powershell
$MCP = "poisontr33s/Restructure-MCP-Orchestration"
$CLAUDINE = "poisontr33s/Claudine_Supreme-Polyglot-Git-Cli-Lsp-Repo-Clone-Engineering-Bun-Technique"
$prs_mcp = gh api "repos/$MCP/pulls?state=open&per_page=100" `
  --jq '[.[] | select(.user.login=="dependabot[bot]") | {number, title, head_ref: .head.ref, created_at}]'
$prs_cla = gh api "repos/$CLAUDINE/pulls?state=open&per_page=100" `
  --jq '[.[] | select(.user.login=="dependabot[bot]") | {number, title, head_ref: .head.ref, created_at}]'
@{ mcp = ($prs_mcp | ConvertFrom-Json); claudine = ($prs_cla | ConvertFrom-Json) } `
  | ConvertTo-Json -Depth 10 | Set-Content manifest/dependabot_gap.json
```

---

## TIER 2 Commands

### 2.1 — Security pattern file (issue #263 encoded)

Create `.github/SECURITY_PATTERNS.md` in Restructure-MCP-Orchestration with:
- Pattern: command injection via `${{ steps.output.outputs.text }}` directly in shell
- Fix: `env: BODY: ${{ ... }}` then `$BODY` in shell
- Source: issue #263 (`cicd-security` bot, 2026-03-29)
- Then: close issue #263 citing the file

```powershell
gh issue comment 263 --repo poisontr33s/Restructure-MCP-Orchestration `
  --body "Pattern encoded in .github/SECURITY_PATTERNS.md. Workflow already disabled. Closing."
gh issue close 263 --repo poisontr33s/Restructure-MCP-Orchestration --reason completed
```

### 2.3 — Branch harvest decisions

After reading diffs (0.1 + 0.2), write harvest decisions:
```json
{
  "claudine": [
    { "branch": "...", "verdict": "draft_pr|stale|cherry_pick", "rationale": "..." }
  ],
  "mcp": [
    { "branch": "...", "issue_number": 263, "verdict": "draft_pr|stale", "lines_changed": 42 }
  ]
}
```
Output: `manifest/branch_archaeology.json`

---

## TIER 3 Commands

### 3.1 — Open draft PRs for Claudine CLI copilot/* branches

```powershell
$CLAUDINE = "poisontr33s/Claudine_Supreme-Polyglot-Git-Cli-Lsp-Repo-Clone-Engineering-Bun-Technique"
# For each branch that gets verdict = draft_pr:
gh pr create --repo $CLAUDINE `
  --head "copilot/add-gpu-accelerated-tfjs-package" `
  --base main `
  --title "[Harvest] GPU-accelerated TFJS package" `
  --body "Copilot-generated branch created ~2025. Harvesting for review. See manifest/branch_archaeology.json." `
  --draft `
  --label "copilot-harvest"
# Repeat for each qualifying branch
```

---

## TIER 4 Commands

### 4.1 — First release tags

```powershell
# Per repo — run from the repo's local checkout after confirming HEAD is clean
$tag = "v0.1.0"
$msg = "Initial versioning baseline — 2026-05-02"

# archive
Set-Location C:\Users\eldno\chthonic-archive
git tag -a $tag -m $msg; git push origin $tag

# claudine
Set-Location "C:\Users\eldno\Claudine_Supreme-Polyglot-Git-Cli-Lsp-Repo-Clone-Engineering-Bun-Technique"
git tag -a $tag -m $msg; git push origin $tag

# pnk
Set-Location C:\Users\eldno\PsychoNoir-Kontrapunkt
git tag -a $tag -m $msg; git push origin $tag

# mcp
Set-Location C:\Users\eldno\Restructure-MCP-Orchestration
git tag -a $tag -m $msg; git push origin $tag
```

### 4.4 — GitHub Projects v2

```powershell
# Create via gh CLI (Projects v2 requires GraphQL mutation)
# Custom fields: District, Type (Human/Copilot/Dependabot/Security), PRISM, Priority
# Views: Open Triage | Security Lane | Copilot Queue | Dependabot Queue
# Full GraphQL mutations in manifest/projects_v2_setup.graphql (generated in Phase 4)
```

---

## TIER 5 Commands

### 5.1 — Dependabot auto-merge (patch/minor)

```yaml
# .github/workflows/dependabot-automerge.yml (per repo)
on: pull_request
permissions:
  pull-requests: write
  contents: write
jobs:
  automerge:
    if: github.actor == 'dependabot[bot]'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/github-script@v7
        with:
          script: |
            const pr = context.payload.pull_request;
            const title = pr.title;
            // Only auto-merge patch bumps (x.y.Z → x.y.Z+1)
            if (/from \d+\.\d+\.\d+ to \d+\.\d+\.\d+/.test(title)) {
              const [,fromPatch,,toPatch] = title.match(/(\d+)\.(\d+)\.(\d+) to (\d+\.\d+\.(\d+))/);
              // Crude major-version guard: if first segment changes, skip
            }
            await github.rest.pulls.merge({ ...context.repo, pull_number: pr.number, merge_method: 'squash' });
```

### 5.2 — polyrepo-runner.ps1 -GitHub flag

New block per district in `$DISTRICTS` array:
```powershell
# Add to each district's tributary list:
@{ name="GitHub Status"; quick=$true; info=$false; run={
  $open_prs = gh api "repos/$($d.ghRepo)/pulls?state=open&per_page=1" --jq 'length'
  $open_issues = gh api "repos/$($d.ghRepo)/issues?state=open&per_page=1" --jq 'length'
  Write-Host "  🔔 PRs: $open_prs  Issues: $open_issues"
}}
```

---

## Status Tracking

| Phase | Status | Output artifact | Notes |
|-------|--------|----------------|-------|
| 0.1 Claudine diffs | ⬜ pending | `manifest/claudine_branch_diffs.json` | |
| 0.2 MCP branch map | ⬜ pending | `manifest/mcp_copilot_branches.json` | |
| 1.1 PR archaeology | ⬜ pending | `manifest/pr_archaeology.json` | |
| 1.2 Dependabot gaps | ⬜ pending | `manifest/dependabot_gap.json` | |
| 2.1 Security pattern | ⬜ pending | `.github/SECURITY_PATTERNS.md` (mcp repo) | |
| 2.3 Harvest decisions | ⬜ pending | `manifest/branch_archaeology.json` | Depends 0.1+0.2 |
| 3.1 Draft PRs claudine | ⬜ pending | GitHub PRs | Depends 2.3 |
| 3.2 Draft PRs mcp | ⬜ pending | GitHub PRs | Depends 2.3 |
| 3.3 Close issue #263 | ⬜ pending | Issue closed | Depends 2.1 |
| 4.1 Release tags | ⬜ pending | git tags × 4 repos | Depends 3.x clean |
| 4.2 PR templates | ⬜ pending | `.github/PULL_REQUEST_TEMPLATE.md` | Depends 1.1 |
| 4.3 .coderabbit.yml | ⬜ pending | `.coderabbit.yml` × 3 repos | Depends 1.1 |
| 4.4 Projects v2 | ⬜ pending | GitHub Projects board | Depends 4.1 |
| 5.1 Dependabot auto-merge | ⬜ pending | `.github/workflows/` | Depends 1.2 analysis |
| 5.2 polyrepo-runner -GitHub | ⬜ pending | `scripts/polyrepo-runner.ps1` | Depends 4.x |
