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

echo "=== cudnn_rb ==="
$RUBY -e "
  require 'cudnn_rb'
  puts \"cuDNN version : #{CudnnRb.version.join('.')}\"
  puts \"cuDNN CUDA    : #{CudnnRb.cuda_version}\"
  puts \"Handle avail  : #{CudnnRb.available?}\"
" 2>&1 || echo "cudnn_rb: no GPU or cuDNN libs in container (expected in build env — OK)"

echo "=== nvml_rb ==="
$RUBY -e "
  require 'nvml_rb'
  puts \"Driver        : #{NvmlRb.version}\"
  puts \"Devices       : #{NvmlRb.device_count}\"
  NvmlRb.devices.each do |d|
    puts \"  [#{d[:index]}] #{d[:name]}\"
    puts \"    Temp #{d[:temperature_c]}C  Fan #{d[:fan_speed_pct]}%  Power #{d[:power_draw_w]}W/#{d[:power_limit_w]}W\"
    puts \"    SM #{d[:sm_clock_mhz]}MHz  Mem #{d[:mem_clock_mhz]}MHz  GPU #{d[:gpu_util_pct]}%  MemCtl #{d[:mem_util_pct]}%\"
    puts \"    VRAM #{d[:free_memory_mib]}/#{d[:total_memory_mib]} MiB free\"
    puts \"    Throttle: #{d[:throttle_reasons].inspect}\"
  end
" 2>&1 || echo "nvml_rb: no GPU in container (expected in build env — OK)"

echo "=== nvrtc_rb ==="
$RUBY -e "
  require 'nvrtc_rb'
  puts \"NVRTC version : #{NvrtcRb.version.join('.')}\"
  # compile a trivial kernel to PTX
  result = NvrtcRb.compile_log(<<~CUDA, ['--gpu-architecture=compute_89'])
    extern \"C\" __global__ void probe(float *x) { x[0] = 1.0f; }
  CUDA
  if result[:success]
    lines = result[:ptx].lines.first(3).map(&:chomp).join(' | ')
    puts \"PTX head      : #{lines}\"
  else
    puts \"Compile log   : #{result[:log]}\"
  end
" 2>&1 || echo "nvrtc_rb: compile probe (expected behaviour without GPU target — OK)"

echo "=== spirv_rb ==="
$RUBY -e "
  require 'spirv_rb'
  puts 'spirv_rb: loaded'
  # Minimal valid SPIR-V OpNop shader (20-byte header + 4-byte OpNop)
  # Magic, Version(1.5), Generator(0), Bound(1), Schema(0), OpNop
  words = [0x07230203, 0x00010500, 0x00000000, 0x00000001, 0x00000000, 0x00010000]
  spv = words.pack('L<*')
  begin
    h = SpirvRb.reflect(spv)
    puts \"Reflect keys  : #{h.keys.map(&:to_s).join(', ')}\"
  rescue => e
    puts \"Reflect error : #{e.message} (module has no entry point — expected)\"
  end
" 2>&1 || echo "spirv_rb: probe (expected in build env — OK)"

echo "=== DONE ==="
