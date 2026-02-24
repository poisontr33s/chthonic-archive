#!/usr/bin/env pwsh

# ╔════════════════════════════════════════════════════════════════════════════
# ║ THE DECORATOR'S BLESSING: kcp_template.ps1
# ╠════════════════════════════════════════════════════════════════════════════
# ║ Wedjat-Quipu Spectrum: GREEN
# ║ Temple-Ayllu Zone: 📜 THE SCRIPTORIUM
# ║ Ogdoad-Ceque Radiance:
# ║   └─◄ docs/standards/KCP_PROTOCOL_ONTOLOGY.md
# ╚════════════════════════════════════════════════════════════════════════════

<#
.SYNOPSIS
Canonical KCP PowerShell Template (Stratum 1 + Stratum 2).

.DESCRIPTION
Character-perfect reference boilerplate demonstrating the complete KCP
two-stratum header for PowerShell files. This template passes Get-Help
parsing without error. All custom @Tag values reside inside the .NOTES
block to avoid breaking the PowerShell Comment-Based Help parser.

USAGE: Copy this header into new .ps1 files and replace placeholder
values with file-specific content.

CARTOUCHE FIELD REFERENCE:
  Artifact Name         - THE DECORATOR'S BLESSING: filename
  Wedjat-Quipu Spectrum - WHITE | ORANGE | RED | BLUE | BLACK | GOLD | GREEN
  Temple-Ayllu Zone     - See KCP_PROTOCOL_ONTOLOGY.md section 4.2
  Ogdoad-Ceque Radiance - dependency path(s) or (Standalone)

KHIPU FIELD REFERENCE (all inside .NOTES):
  @SID            - UPPER_SNAKE: [PREFIX]_[NAME]_V[N]
  @Shabti         - CLI Script | Automation Script | Config | etc.
  @Heka-Ayni      - CONCEPT_domain (optional)
  @Ankh-Tinku     - STATE_outcome (optional)
  @Purpose        - Unbounded free text

.NOTES
@SID:           STD_KCP_TEMPLATE_POWERSHELL_V1
@Shabti:        Standard
@Heka-Ayni:     CONCEPT_KCP_CANONIZATION
@Ankh-Tinku:    STATE_KCP_TEMPLATE_RATIFIED
@Purpose:       Canonical reference template for KCP-compliant PowerShell
                files. Demonstrates correct placement of Khipu tags
                within the .NOTES section of Comment-Based Help,
                preserving Get-Help compatibility.
#>
