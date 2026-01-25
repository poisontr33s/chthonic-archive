# 🎯 AUTONOMOUS COORDINATOR QUICKREF

**Version:** 1.0.0  
**Status:** ✅ OPERATIONAL  
**Last Updated:** January 1, 2026

---

## 🚀 Quick Start

### Run Coordinator Manually
```powershell
cd C:\Users\erdno\chthonic-archive
uv run python autonomous_coordinator.py
```

### View Latest Health Report
```powershell
Get-ChildItem health_reports | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content
```

### Check Topology Stats
```powershell
Get-Content topology_summary.md
```

### View SSOT Status
```powershell
Get-Content .dcrp_state.json | ConvertFrom-Json
```

---

## 📋 What It Does (4 Phases)

### Phase 1: Lane Validation
- Checks Lineage A/B/C operational status
- Validates template population
- Reports lane health

### Phase 2: Artifact Regeneration
- Runs `decorator_cross_ref_production.py` (DCRP)
- Runs `unified_topology.py` (cross-lane graph)
- Updates MCP schemas (Phase 5 feature - currently SKIPPED)

### Phase 3: SSOT Hash Verification
- Computes SHA-256 hashes of SSOT files
- Compares against baseline (`.dcrp_state.json`)
- Logs drift events to `logs/ssot_drift.log`
- Creates GitHub issue stub if drift detected

### Phase 4: Health Report
- Generates `HEALTH_REPORT_<timestamp>.md`
- Summarizes repository metrics
- Reports lane status
- Lists SSOT integrity status

---

## 🔧 Configuration

### Files Monitored (SSOT)
Edit in `ssot_immunity.py`:
```python
SSOT_FILES = [
    ".github/copilot-instructions.md",
    "ankh.md",
    "ANKHOLOGY.md",
    "ANKH_README.md",
]
```

### Timeouts
Edit in `autonomous_coordinator.py`:
```python
# DCRP regeneration timeout
timeout=120  # Line 115

# Topology regeneration timeout
timeout=60   # Line 139

# Health report timeout
timeout=30   # Line 222
```

---

## 📊 Key Metrics (Current)

```
Topology Nodes:      10,110
Topology Edges:       9,165
DCRP Files:             949
Cycle Time:          22.6s
SSOT Files:               4
Status:            HEALTHY
```

---

## 🐛 Troubleshooting

### Coordinator Fails
```powershell
# Check logs
Get-Content logs/github_issues/*.json

# Re-run DCRP manually
uv run python decorator_cross_ref_production.py

# Re-run topology manually
uv run python unified_topology.py
```

### SSOT Drift Detected
```powershell
# View drift log
Get-Content logs/ssot_drift.log

# Check baseline
Get-Content .dcrp_state.json | ConvertFrom-Json

# Reset baseline (CAUTION: Only if drift is intentional)
Remove-Item .dcrp_state.json
uv run python autonomous_coordinator.py  # Reinitializes baseline
```

### Unicode Errors
✅ **FIXED** - Encoding parameters added to all subprocess calls

If errors persist:
```powershell
# Check PowerShell encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Re-run coordinator
uv run python autonomous_coordinator.py
```

---

## 🔮 Future Enhancements (Phase 4)

### P1: Cross-Lane Cycle Detection
Detect circular dependencies across lane boundaries

### P2: GitHub Issue Creation via MCP
Replace local JSON stubs with real GitHub API integration

### P3: Incremental Topology Updates
Update only changed nodes/edges (5-10x speedup)

### P4: MCP Schema Registry
Centralized schema cache for all MCP tools

---

## 📜 Git Hook Integration (Optional)

### Setup Post-Commit Hook
```bash
# .git/hooks/post-commit
#!/usr/bin/env bash
uv run python autonomous_coordinator.py || echo "Coordinator failed" >&2
```

### Make Executable
```bash
chmod +x .git/hooks/post-commit
```

### Test Hook
```bash
git commit --allow-empty -m "Test coordinator hook"
# Coordinator should run automatically
```

---

## 🎓 Understanding the Output

### Successful Run
```
🤖 Autonomous Coordinator: Starting validation cycle...

🔍 Phase 1: Validating lineage lanes...
  ✅ Lineage A: OPERATIONAL
  ✅ Lineage B: COMPLETE
  ✅ Lineage C: COMPLETE

♻️  Phase 2: Regenerating artifacts...
  ✅ DCRP: SUCCESS
  ✅ Topology: SUCCESS
  ⚠️ MCP Schemas: SKIPPED

🔐 Phase 3: Verifying SSOT hash...
  ✅ No drift detected

📊 Phase 4: Generating health report...
📊 Health report generated: HEALTH_REPORT_<timestamp>.md

✅ Autonomous Coordinator: Cycle complete
```

### Error States

**Lane Validation Error:**
```
⚠️ Lineage A: ERROR
Message: Template missing
```
→ Check `dumpster-dive/intake/templates/lineage-A-template/manifest.yml` exists

**Artifact Regeneration Error:**
```
❌ DCRP: ERROR
Message: DCRP failed: <stderr output>
```
→ Run `uv run python decorator_cross_ref_production.py` manually to debug

**SSOT Drift Detected:**
```
⚠️ DRIFT DETECTED: HIGH
📝 GitHub issue logged: issue_<timestamp>.json
```
→ Check `logs/ssot_drift.log` for details

---

## 📚 Related Documentation

- **Session 3 Complete:** `AUTONOMOUS_SESSION_3_COMPLETE.md`
- **Execution Report:** `AUTONOMOUS_SESSION_3_EXECUTION_COMPLETE.md`
- **Mission Report:** `AUTONOMOUS_SESSION_3_MISSION_REPORT.md`
- **Deep Research:** `AUTONOMOUS_SESSION_3_DEEP_RESEARCH.md`
- **DCRP Analysis:** `DCRP_PRODUCTION_ANALYSIS.md`
- **Topology Map:** `topology_map.md`
- **Topology Summary:** `topology_summary.md`

---

## 🔥 Emergency Commands

### Force SSOT Baseline Reset
```powershell
Remove-Item .dcrp_state.json -Force
uv run python autonomous_coordinator.py
```

### Regenerate All Artifacts
```powershell
uv run python decorator_cross_ref_production.py
uv run python unified_topology.py
uv run python health_report.py
```

### Clean Generated Files
```powershell
Remove-Item topology_graph.json -Force
Remove-Item topology_map.md -Force
Remove-Item topology_summary.md -Force
Remove-Item dependency_graph_production.json -Force
Remove-Item health_reports/*.md -Force
```

---

**The Nervous System is alive. Use these commands to monitor its heartbeat. 👑💀⚜️**

**Last validated:** January 1, 2026 08:50 UTC
