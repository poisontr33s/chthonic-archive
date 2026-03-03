# @SID: FORGE_RUBY_CLUSTER_REGISTRY_V1
# Purpose: Ruby mirror of recovered Python cluster hotspots.
Cluster = Struct.new(:source_file, :fragment_count, :sample_lines, keyword_init: true)

RECOVERED_CLUSTERS = [
  Cluster.new(source_file: 'scripts/poe_transport_audit.py', fragment_count: 21, sample_lines: ['def probe_sdk(account: str, bot: str, prompt: str) -> ProbeResult:', '    rc, out, err = run_cmd(', '        [']),
  Cluster.new(source_file: 'scripts/poe_lane.py', fragment_count: 15, sample_lines: ['"""', 'Poe lane helper (OpenAI-compatible endpoint).', 'Modes:']),
  Cluster.new(source_file: 'scripts/code_scent.py', fragment_count: 9, sample_lines: ["# ║  THE DECORATOR'S BLESSING: code_scent.py                                      ║", '# ║  Python module: analyze_scent                                                 ║', '# ╠═══════════════════════════════════════════════════════════════════════════════╣']),
  Cluster.new(source_file: 'scripts/background_services.py', fragment_count: 8, sample_lines: ['Chthonic Archive - Background Services', '=======================================', 'A collection of background services that supplement the main development workflow.']),
  Cluster.new(source_file: 'mas_mcp/mas_diagnostics.py', fragment_count: 8, sample_lines: ["║  MAS-MCP DIAGNOSTICS: The Living Layer's Self-Examination            ║", '║══════════════════════════════════════════════════════════════════════║', '║                                                                      ║']),
  Cluster.new(source_file: 'scripts/mandala_topology.py', fragment_count: 7, sample_lines: ['# ╔════════════════════════════════════════════════════════════════════════════╗', "# ║  THE DECORATOR'S BLESSING: mandala_topology.py                           ║", '# ║  Python module: _load_graph, _top_centrality, _build_report, _render_text, reveal_sacred_geometry, _write_output_json... ║']),
  Cluster.new(source_file: 'scripts/upcycle_audit.py', fragment_count: 6, sample_lines: ['# ╔════════════════════════════════════════════════════════════════════════════╗', "# ║  THE DECORATOR'S BLESSING: upcycle_audit.py                              ║", '# ║  Python module: COMMENT_MARKERS, SKIP_PATTERNS, EXEMPT_FROM_NOMINATION, should_skip, analyze_file, scan_paths... ║']),
  Cluster.new(source_file: 'scripts/code_taste.py', fragment_count: 6, sample_lines: ['# ╔════════════════════════════════════════════════════════════════════════════╗', "# ║  THE DECORATOR'S BLESSING: code_taste.py                                 ║", '# ║  Python module: analyze_taste                                               ║']),
]

def top_clusters(limit = 10)
  RECOVERED_CLUSTERS.first([limit, 0].max)
end
