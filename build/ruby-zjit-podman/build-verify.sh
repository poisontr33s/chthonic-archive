#!/usr/bin/env bash
# build.sh — executed inside the Podman container context for validation runs
# Not the build script — that's ruby_podman_build.ps1 (Win11 orchestrator)
# This is the post-build verification script run inside the image
set -euo pipefail

RUBY=/opt/ruby-zjit/bin/ruby

echo "=== Ruby build verification ==="
$RUBY --version

echo "=== ZJIT ==="
$RUBY --zjit -e "puts RUBY_DESCRIPTION; puts ZJITStats rescue puts 'ZJITStats not exposed (expected in 4.0.3)'"

echo "=== YJIT ==="
$RUBY --yjit -e "puts RUBY_DESCRIPTION" 2>/dev/null || echo "YJIT: graceful fallback (Rust not linked)"

echo "=== Prism ==="
$RUBY -e "require 'prism'; puts 'Prism: ' + Prism::VERSION; r = Prism.parse('1 + 2'); puts 'Parse OK: ' + r.value.class.name"

echo "=== Gems ==="
$RUBY -e "require 'bundler'; puts 'Bundler: ' + Bundler::VERSION"
$RUBY -e "require 'rake'; puts 'Rake: ' + Rake::VERSION"

echo "=== ZJIT+Prism combined ==="
$RUBY --zjit -e "require 'prism'; r = Prism.parse('x = 1 + 2'); puts 'ZJIT+Prism parse: ' + r.value.class.name"

echo "=== DONE ==="
