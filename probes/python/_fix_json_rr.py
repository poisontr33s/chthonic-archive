#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import pathlib

f = pathlib.Path(r"C:\Users\eldno\chthonic-archive\dev\tabbyAPI\.venv\Lib\site-packages\formatron\formats\json.py")
t = f.read_text(encoding="utf-8")

# Fix double r-prefix introduced by idempotency bug in previous patch run
t = t.replace("rr'\\A'", "r'\\A'").replace("rr'\\z'", "r'\\z'")
f.write_text(t, encoding="utf-8")

line = t.splitlines()[115]
print("line 116:", repr(line))
assert "rr'" not in line, "STILL BROKEN"
print("OK — r-string fixed")
