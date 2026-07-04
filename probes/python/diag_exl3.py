#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import traceback, sys
try:
    import exllamav3
    print("exllamav3 import: OK")
    print("exllamav3 path:", exllamav3.__file__)
except Exception:
    print("exllamav3 import: FAILED")
    traceback.print_exc()

# Also check the .so directly
try:
    import exllamav3.exllamav3_ext as ext  # noqa
    print("exllamav3_ext: OK")
except Exception:
    print("exllamav3_ext: FAILED")
    traceback.print_exc()

# Check flash_attn
try:
    import flash_attn
    print("flash_attn: OK")
except Exception as e:
    print(f"flash_attn: FAILED — {e}")

# Check GLIBCXX
import subprocess
result = subprocess.run(
    ["strings", "/workspace/.venv/lib/python3.14/site-packages/exllamav3/exllamav3_ext.cpython-314-x86_64-linux-gnu.so"],
    capture_output=True, text=True
)
glibcxx_needed = [line for line in result.stdout.splitlines() if "GLIBCXX" in line]
print("GLIBCXX needed in .so:", sorted(set(glibcxx_needed)))

# Check what libstdc++ provides
result2 = subprocess.run(["strings", "/usr/lib/x86_64-linux-gnu/libstdc++.so.6"],
    capture_output=True, text=True)
glibcxx_have = [line for line in result2.stdout.splitlines() if "GLIBCXX_3.4" in line and not line.startswith(" ")]
print("GLIBCXX provided:", sorted(set(glibcxx_have)))
