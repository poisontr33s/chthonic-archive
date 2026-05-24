# Probe Variant Audit Report

**Date:** 2026-01-06  
**Scanner:** `scripts/compare_probe_variants.ps1`  
**Canonical Hash:** `636383C0DB1F4ACDF539335337C322FD9E4F30F429A15B46C647876D29918116`

---

## Summary

| Metric | Count |
|--------|-------|
| Total probe-like files | 6 |
| Canonical (compliant) | 1 |
| Variants with forbidden logic | 4 |
| Action required | 2 |

---

## File Inventory

### ✓ Canonical (ABI-Stable)

**File:** `scripts/shell_capabilities.ps1`  
**Hash:** `636383C0...8116`  
**Status:** **CANONICAL** - DO NOT MODIFY  
**Purpose:** Minimal environment probe for AI agents  
**Features:**
- Pure JSON output (no logging)
- No logic constructs (no if/foreach/while/switch/try/catch)
- Code ratio: 92% (minimal comments)
- Header: `# DO NOT EDIT — ABI STABLE PROBE`

---

### ⚠ Variants Requiring Action

#### 1. `scripts/sfs.ps1`

**Hash:** `FA8B25C22E0885C0FC9932B966E311DF66C9E57790CFB55F441688E942720BEB`  
**Status:** VARIANT (obsolete, pre-canonical form)  
**Issues:**
- Different implementation than canonical (adds timestamp, script_path, pwsh_edition)
- Missing ABI header
- No forbidden logic, but not identical to canonical

**Recommendation:** **RENAME** to `scripts/sfs_obsolete.ps1` or **ARCHIVE** to `dumpster-dive/archive/probe-variants/`

**Justification:** While technically compliant (no forbidden logic), having multiple "shell_capabilities.ps1" variants creates confusion. The canonical form is intentionally minimal (12 lines). This variant adds fields that may encourage future modification.

---

#### 2. `scripts/probe_toolchain_path.ps1`

**Hash:** `3BD8EDDCD932B8FE558CB5B7B61E454221693EF2BB66E389DDE5BB808ABB9D79`  
**Status:** VARIANT (different purpose - PATH discovery tool)  
**Issues:**
- Contains forbidden logic constructs (if/foreach/while)
- 220 lines (complex, not minimal)
- Purpose differs from probe (constructs PATH, writes files)

**Recommendation:** **NO ACTION** - This is a legitimate utility tool, not a probe variant

**Justification:** Despite similar naming (`probe_` prefix), this serves a different function (PATH construction/toolchain discovery). Should remain as-is but could benefit from documentation clarifying it's NOT the canonical probe.

---

### ✓ Variants - No Action Required

#### 3. `scripts/validate_probe.ps1`

**Hash:** `A9A81E862A3CFB62BA445AA79722D218EB250F1463893B3B6DE13B9F07B6600D`  
**Status:** VALIDATOR (intentionally contains logic)  
**Purpose:** Automated probe contract validation  
**Forbidden constructs:** Expected (validation requires if/foreach)  
**Recommendation:** NO ACTION - Working as designed

---

#### 4. `scripts/compare_probe_variants.ps1`

**Hash:** `63CCE9A35F7E22A408A02A9AB46F09D71B906327E24605A4B4FC20E50D58D21A`  
**Status:** SCANNER (intentionally contains logic)  
**Purpose:** Repository probe variant detection  
**Forbidden constructs:** Expected (scanning requires if/foreach/while)  
**Recommendation:** NO ACTION - Working as designed

---

#### 5. `dumpster-dive/intake/claudine-harvest/2919D506B1758C9B__Microsoft.PowerShell_profile.ps1`

**Hash:** `2919D506B1758C9BFF51963437E0FE361766C4C318CC274D41FD094398A3174D`  
**Status:** ARCHIVED (PowerShell profile, not a probe)  
**Purpose:** User profile captured during claudine harvest  
**Forbidden constructs:** Expected (profiles contain logic)  
**Recommendation:** NO ACTION - Archive artifact, correctly placed in `dumpster-dive/intake/`

---

## Action Plan

### High Priority

1. **Archive/rename `scripts/sfs.ps1`**
   ```powershell
   # Option A: Rename to mark obsolete
   Rename-Item scripts/sfs.ps1 scripts/sfs_obsolete.ps1
   
   # Option B: Archive to dumpster-dive
   mkdir -p dumpster-dive/archive/probe-variants
   Move-Item scripts/sfs.ps1 dumpster-dive/archive/probe-variants/sfs_pre-canonical.ps1
   ```

2. **Add clarifying comment to `probe_toolchain_path.ps1`**
   - Add header: `# NOTE: This is NOT the canonical probe (see shell_capabilities.ps1)`
   - Purpose: Prevent confusion for agents scanning for "probe" files

### Medium Priority

3. **Document probe ecosystem in README**
   - Create `scripts/README.md` explaining:
     - `shell_capabilities.ps1` = canonical probe
     - `validate_probe.ps1` = validator
     - `compare_probe_variants.ps1` = scanner
     - `probe_toolchain_path.ps1` = PATH discovery (different purpose)

### Low Priority

4. **Add CI validation** (already created: `.github/workflows/validate-probe.yml`)
5. **Run full upcycle audit** to identify other governance violations

---

## Verification

After addressing `sfs.ps1`, re-run scanner to verify cleanup:

```powershell
.\scripts\compare_probe_variants.ps1
# Expected: 5 total files (sfs.ps1 removed or renamed)
# Expected: 1 canonical, 0 action-required variants
```

---

## References

- **Canonical Probe:** `scripts/shell_capabilities.ps1`
- **Validator:** `scripts/validate_probe.ps1`
- **Scanner:** `scripts/compare_probe_variants.ps1`
- **CI Workflow:** `.github/workflows/validate-probe.yml`
- **Documentation:** `docs/PWSH_RULES.md` (lines 180-268)
- **Upcycle Auditor:** `scripts/upcycle_audit.py`

---

**Generated by:** `scripts/compare_probe_variants.ps1`  
**Run:** `.\scripts\compare_probe_variants.ps1 > reports/probe_variant_audit.md`

