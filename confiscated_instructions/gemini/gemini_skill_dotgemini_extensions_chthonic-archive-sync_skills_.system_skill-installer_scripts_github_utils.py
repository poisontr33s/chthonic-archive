#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# SID:           TOOL_FETCH_COMMENTS_V1
# Shabti:        CLI Script
# Purpose:       Fetch all PR conversation comments + reviews + review threads (inline threads) for the PR associated with the current git branch, by shelling out to  gh api graphql

# ════════════════════════════════════════════════════════════════════════════
# ═ THE DECORATOR'S BLESSING: fetch_comments.py
# ═ Wedjat-Quipu Spectrum: WHITE
# ═ Temple-Ayllu Zone: 🔥 THE FOUNDRY
# ═ Ogdoad-Ceque Radiance:
# ═   └─◄ (Standalone)
# ════════════════════════════════════════════════════════════════════════════

"""
Shared GitHub helpers for skill install scripts.
"""

from __future__ import annotations

import os
import urllib.request


def github_request(url: str, user_agent: str) -> bytes:
    headers = {"User-Agent": user_agent}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return resp.read()


def github_api_contents_url(repo: str, path: str, ref: str) -> str:
    return f"https://api.github.com/repos/{repo}/contents/{path}?ref={ref}"
