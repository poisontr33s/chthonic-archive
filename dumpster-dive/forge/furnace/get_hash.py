#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import hashlib
import unicodedata

def canonicalize(text: str) -> str:
    # Standardize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Strip trailing whitespace from each line
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)
    # NFC normalization
    text = unicodedata.normalize('NFC', text)
    return text.strip()

def ssot_hash(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    canonical = canonicalize(content)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

import sys
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_REPO_ROOT))
from scripts.lib.ssot_paths import SSOT_POINTER

print(ssot_hash(SSOT_POINTER))
