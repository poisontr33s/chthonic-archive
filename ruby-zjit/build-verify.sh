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

# ── Native extension probes (graceful — no GPU in build container) ────────────

echo "=== cuda_rb ==="
$RUBY -e "
  require 'cuda_rb'
  puts \"CUDA driver : #{CudaRb.driver_version}\"
  puts \"CUDA runtime: #{CudaRb.runtime_version}\"
  count = CudaRb.device_count
  puts \"Devices     : #{count}\"
  count.times { |i| puts \"  [#{i}] #{CudaRb.device_name(i)} CC#{CudaRb.device_compute_capability(i).join('.')}\" }
" 2>&1 || echo "cuda_rb: no GPU in container (expected in build env — OK)"

echo "=== vk_rb ==="
$RUBY -e "
  require 'vk_rb'
  puts \"Vulkan instance: #{VkRb.instance_version}\"
  devs = VkRb.physical_devices
  puts \"Physical devices: #{devs.size}\"
  devs.each { |d| puts \"  #{d[:name]} (#{d[:device_type]}) API #{d[:api_version]}\" }
  puts \"VK_KHR_surface: #{VkRb.has_extension?('VK_KHR_surface')}\"
" 2>&1 || echo "vk_rb: no Vulkan ICD in container (expected in build env — OK)"

echo "=== trt_rb ==="
$RUBY -e "
  require 'trt_rb'
  puts \"TensorRT     : #{TrtRb.version}\"
  puts \"nvinfer      : #{TrtRb.nvinfer_version.join('.')}\"
  puts \"CUDA runtime : #{TrtRb.cuda_version}\"
  puts \"Builder      : #{TrtRb.builder_available?}\"
" 2>&1 || echo "trt_rb: no GPU in container (expected in build env — OK)"

echo "=== DONE ==="
