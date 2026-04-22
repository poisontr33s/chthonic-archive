{
  "scan_time": "2026-03-24T16:17:01.047862",
  "summary": {
    "total_files": 43,
    "total_size": 1453567,
    "extension_counts": {
      "(no extension)": 1,
      ".md": 11,
      ".toml": 4,
      ".json": 13,
      ".rs": 1,
      ".lock": 3,
      ".py": 6,
      ".txt": 2,
      ".log": 1,
      ".o": 1
    }
  },
  "versioned_files": [],
  "potential_duplicates": [
    {
      "file1": "$null",
      "file2": "kcp_batch1_verify.json",
      "similarity": 1.0
    }
  ],
  "missing_metadata": [
    "claude_test.py",
    "get_hash.py",
    "purify_ssot.py",
    "strip_post_ssot.py",
    "strip_ssot.py",
    "strip_ssot_v2.py"
  ],
  "empty_files": [
    "$null",
    "kcp_batch1_verify.json"
  ],
  "large_files": [
    {
      "name": "log.txt",
      "extension": ".txt",
      "size": 839630,
      "modified": "2026-03-16T15:37:34.050530",
      "has_metadata": false,
      "version_pattern": ""
    }
  ],
  "recommendations": [
    "DELETE: 1 potential duplicate file pairs detected. Review and remove redundant copies.",
    "UPDATE: 6 code files lack metadata headers. Add FILE METADATA blocks for traceability.",
    "DELETE: 2 empty files found. Remove or populate with content.",
    "REVIEW: 1 files exceed 500KB. Consider compression or moving to separate storage.",
    "RELOCATE: 6 Python files in root directory. Move to scripts/ for better organization."
  ]
}