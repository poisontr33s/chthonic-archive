#!/usr/bin/env bash

# chthonic - CLI router for chthonic-archive tooling
#
# @SID:           TOOL_CHTHONIC_ROUTER_BASH
# @Type:          Router Script
# @Context:       Infrastructure / CLI Entry Point
# @SessionOrigin: CONTINUATION_2026_01_27
# @Implements:    ROADMAP_TOOL_CONSOLIDATION_2026_01_27
#
# Bash-based router for Unix/Linux/macOS platforms.
# Dispatches to Python modules in lib/.
#
# Usage: chthonic <command> [<args>]
#
# Commands:
#   audit       Analyze root directory health
#   compact     Condense markdown files
#   extract     Extract session JSONL content
#   resolve     Resolve Semantic IDs (@SID)
#   map         Generate codebase inventory
#   analyze     Pattern frequency analysis

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

# Version
VERSION="1.0.0"

# Show help
show_help() {
    cat <<EOF
chthonic v$VERSION - CLI tooling for chthonic-archive

Usage: chthonic [--version] [--help] <command> [<args>]

Commands:
  audit       Analyze root directory health and recommend cleanups
  compact     Condense markdown files using noise pattern matching
  extract     Extract valuable content from session JSONL files
  resolve     Resolve Semantic IDs (@SID) to file paths
  map         Generate codebase inventory and dependency graph
  analyze     Frequency analysis of line patterns (diagnostic)

Options:
  --version   Show version
  --help      Show this help

Run 'chthonic <command> --help' for command-specific help.
EOF
}

# Command dispatch
dispatch() {
    local cmd="$1"
    shift
    
    case "$cmd" in
        audit|compact|extract|resolve|map|analyze)
            cd "$SCRIPT_DIR"
            exec uv run python -m "lib.$cmd" "$@"
            ;;
        --version)
            echo "chthonic v$VERSION"
            exit 0
            ;;
        --help|-h|help)
            show_help
            exit 0
            ;;
        *)
            echo "Error: Unknown command '$cmd'" >&2
            echo "Run 'chthonic --help' for usage." >&2
            exit 1
            ;;
    esac
}

# Main entry
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

dispatch "$@"
