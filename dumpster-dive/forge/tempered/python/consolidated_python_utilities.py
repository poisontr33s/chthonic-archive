# @SID: FORGE_CONSOLIDATED_PYTHON_UTILS_V1
# Purpose: Recovered Python utility registry from corpse-vault evolutionary hotspots.
# Source-Files: scripts/poe_transport_audit.py, scripts/poe_lane.py, scripts/code_scent.py, scripts/background_services.py, mas_mcp/mas_diagnostics.py, scripts/mandala_topology.py, scripts/upcycle_audit.py, scripts/code_taste.py, scripts/ssot_hash.py, scripts/run_cycle.py, scripts/github_voice.py, scripts/code_texture.py
# Pathway: corpse-vault/python -> cluster audit -> utility registry module
# Kept: Cluster metadata, representative lines, and search helpers.
# Discarded: Broken fragment boundaries and deleted implementation glue.
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecoveredPythonCluster:
    source_file: str
    fragment_count: int
    sample_lines: tuple[str, ...]


RECOVERED_PYTHON_CLUSTERS = [
    RecoveredPythonCluster(
        source_file='scripts/poe_transport_audit.py',
        fragment_count=21,
        sample_lines=('def probe_sdk(account: str, bot: str, prompt: str) -> ProbeResult:', '    rc, out, err = run_cmd(', '        [', '            "uv",'),
    ),
    RecoveredPythonCluster(
        source_file='scripts/poe_lane.py',
        fragment_count=15,
        sample_lines=('"""', 'Poe lane helper (OpenAI-compatible endpoint).', 'Modes:', '- models: list accessible model IDs for the active Poe key.'),
    ),
    RecoveredPythonCluster(
        source_file='scripts/code_scent.py',
        fragment_count=9,
        sample_lines=("# ║  THE DECORATOR'S BLESSING: code_scent.py                                      ║", '# ║  Python module: analyze_scent                                                 ║', '# ╠═══════════════════════════════════════════════════════════════════════════════╣', '# ║  Spectral Frequency: WHITE                                                    ║'),
    ),
    RecoveredPythonCluster(
        source_file='scripts/background_services.py',
        fragment_count=8,
        sample_lines=('Chthonic Archive - Background Services', '=======================================', 'A collection of background services that supplement the main development workflow.', 'These run independently and provide continuous monitoring,'),
    ),
    RecoveredPythonCluster(
        source_file='mas_mcp/mas_diagnostics.py',
        fragment_count=8,
        sample_lines=("║  MAS-MCP DIAGNOSTICS: The Living Layer's Self-Examination            ║", '║══════════════════════════════════════════════════════════════════════║', '║                                                                      ║', '║  "The living layer looks at itself in the mirror of the static      ║'),
    ),
    RecoveredPythonCluster(
        source_file='scripts/mandala_topology.py',
        fragment_count=7,
        sample_lines=('# ╔════════════════════════════════════════════════════════════════════════════╗', "# ║  THE DECORATOR'S BLESSING: mandala_topology.py                           ║", '# ║  Python module: _load_graph, _top_centrality, _build_report, _render_text, reveal_sacred_geometry, _write_output_json... ║', '# ╠════════════════════════════════════════════════════════════════════════════╣'),
    ),
    RecoveredPythonCluster(
        source_file='scripts/upcycle_audit.py',
        fragment_count=6,
        sample_lines=('# ╔════════════════════════════════════════════════════════════════════════════╗', "# ║  THE DECORATOR'S BLESSING: upcycle_audit.py                              ║", '# ║  Python module: COMMENT_MARKERS, SKIP_PATTERNS, EXEMPT_FROM_NOMINATION, should_skip, analyze_file, scan_paths... ║', '# ╠════════════════════════════════════════════════════════════════════════════╣'),
    ),
    RecoveredPythonCluster(
        source_file='scripts/code_taste.py',
        fragment_count=6,
        sample_lines=('# ╔════════════════════════════════════════════════════════════════════════════╗', "# ║  THE DECORATOR'S BLESSING: code_taste.py                                 ║", '# ║  Python module: analyze_taste                                               ║', '# ╠════════════════════════════════════════════════════════════════════════════╣'),
    ),
    RecoveredPythonCluster(
        source_file='scripts/ssot_hash.py',
        fragment_count=6,
        sample_lines=('# ╔════════════════════════════════════════════════════════════════════════════╗', "# ║  THE DECORATOR'S BLESSING: ssot_hash.py                                  ║", '# ║  Python module: canonicalize, ssot_hash, verify_ssot_integrity, main        ║', '# ╠════════════════════════════════════════════════════════════════════════════╣'),
    ),
    RecoveredPythonCluster(
        source_file='scripts/run_cycle.py',
        fragment_count=5,
        sample_lines=('# ╔════════════════════════════════════════════════════════════════════════════╗', "# ║  THE DECORATOR'S BLESSING: run_cycle.py                                  ║", '# ║  Python module: find_workspace_root, WORKSPACE_ROOT, MAS_MCP_ROOT, ARTIFACTS_DIR, GOVERNANCE_DIR, COMPATIBILITY_DIR... ║', '# ╠════════════════════════════════════════════════════════════════════════════╣'),
    ),
    RecoveredPythonCluster(
        source_file='scripts/github_voice.py',
        fragment_count=5,
        sample_lines=('# ╔════════════════════════════════════════════════════════════════════════════╗', "# ║  THE DECORATOR'S BLESSING: github_voice.py                               ║", '# ║  Python module: is_voice_active, broadcast_issue                            ║', '# ╠════════════════════════════════════════════════════════════════════════════╣'),
    ),
    RecoveredPythonCluster(
        source_file='scripts/code_texture.py',
        fragment_count=5,
        sample_lines=('# ╔════════════════════════════════════════════════════════════════════════════╗', "# ║  THE DECORATOR'S BLESSING: code_texture.py                               ║", '# ║  Python module: analyze_texture                                             ║', '# ╠════════════════════════════════════════════════════════════════════════════╣'),
    ),
]

def top_clusters(limit: int = 10) -> list[RecoveredPythonCluster]:
    return RECOVERED_PYTHON_CLUSTERS[: max(limit, 0)]

def search_clusters(keyword: str) -> list[RecoveredPythonCluster]:
    lowered = keyword.lower()
    return [cluster for cluster in RECOVERED_PYTHON_CLUSTERS if lowered in cluster.source_file.lower()]
