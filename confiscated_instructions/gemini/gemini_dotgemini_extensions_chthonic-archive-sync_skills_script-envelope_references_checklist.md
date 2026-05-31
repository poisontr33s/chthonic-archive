# Script-Envelope Checklist

1. Confirm target exists and is within repo.
2. Identify language and expected shebang.
3. Add or repair metadata envelope (top of file).
4. Ensure SID, purpose, exports, cross-references, and flags/modes are present.
5. Normalize shebang if safe.
6. For Python, enforce canonical prologue:
   - `#!/usr/bin/env python3`
   - `#-*- coding: utf-8 -*-`
   - module docstring banner directly below header (preferred)
7. Avoid no-op rewrites (already compliant files must remain untouched).
8. Preserve code semantics.
9. Report updated path + diff summary.
