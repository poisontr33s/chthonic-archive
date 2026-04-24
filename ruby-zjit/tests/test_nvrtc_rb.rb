# frozen_string_literal: true
require 'minitest/autorun'
NVRTC_RB_AVAILABLE = begin; require 'nvrtc_rb'; true; rescue LoadError => e; warn "nvrtc_rb not built: #{e.message}"; false; end

NVRTC_VER = begin; NvrtcRb.version; rescue => e; warn "nvrtc_rb init: #{e}"; [0, 0]; end
NVRTC_OK  = NVRTC_VER[0] > 0

# Minimal kernel — intentionally simple (no device pointers, no CUDA runtime types).
# We only test compilation correctness; no kernel launch needed.
PROBE_KERNEL = <<~CUDA
  extern "C" __global__ void probe(int *out) { *out = 42; }
CUDA

PROBE_OPTS = %w[--gpu-architecture=compute_89].freeze

class TestNvrtcRb < Minitest::Test
  def setup
    skip "nvrtc_rb extension not built — run build_win32.ps1" unless NVRTC_RB_AVAILABLE
  end
  def test_version_returns_pair_array
    v = NvrtcRb.version
    assert_kind_of Array, v
    assert_equal 2, v.size, "version should be [major, minor]"
    v.each { |n| assert_kind_of Integer, n }
  end

  def test_version_major_sane
    skip "NVRTC not available" unless NVRTC_OK
    assert_operator NVRTC_VER[0], :>=, 11,
      "NVRTC major should be >= 11 (CUDA 11+)"
  end

  def test_compile_returns_string
    skip "NVRTC not available" unless NVRTC_OK
    ptx = NvrtcRb.compile(PROBE_KERNEL, PROBE_OPTS)
    assert_kind_of String, ptx
    refute_empty ptx
  end

  def test_compile_ptx_has_magic_marker
    skip "NVRTC not available" unless NVRTC_OK
    ptx = NvrtcRb.compile(PROBE_KERNEL, PROBE_OPTS)
    # All PTX files start with the .version directive
    assert_match(/\.version/, ptx, "PTX output should contain .version directive")
  end

  def test_compile_ptx_contains_kernel_name
    skip "NVRTC not available" unless NVRTC_OK
    ptx = NvrtcRb.compile(PROBE_KERNEL, PROBE_OPTS)
    assert_match(/probe/, ptx, "PTX output should contain kernel name 'probe'")
  end

  def test_compile_raises_on_bad_source
    skip "NVRTC not available" unless NVRTC_OK
    assert_raises(RuntimeError) do
      NvrtcRb.compile("this is not valid CUDA ??? !!!", [])
    end
  end

  def test_compile_error_message_contains_log
    skip "NVRTC not available" unless NVRTC_OK
    err = assert_raises(RuntimeError) do
      NvrtcRb.compile("void bad() { DOES_NOT_EXIST(); }", [])
    end
    # The error message should contain compilation log, not be empty
    refute_empty err.message
  end

  def test_compile_log_returns_hash
    skip "NVRTC not available" unless NVRTC_OK
    result = NvrtcRb.compile_log(PROBE_KERNEL, PROBE_OPTS)
    assert_kind_of Hash, result
    assert result.key?(:ptx),     "compile_log result missing :ptx"
    assert result.key?(:log),     "compile_log result missing :log"
    assert result.key?(:success), "compile_log result missing :success"
  end

  def test_compile_log_success_true_for_valid_kernel
    skip "NVRTC not available" unless NVRTC_OK
    result = NvrtcRb.compile_log(PROBE_KERNEL, PROBE_OPTS)
    assert result[:success], "compile_log should succeed for valid kernel"
    refute_empty result[:ptx]
  end

  def test_compile_log_success_false_for_bad_source
    skip "NVRTC not available" unless NVRTC_OK
    result = NvrtcRb.compile_log("definitely not cuda ??? !!!", [])
    assert_equal false, result[:success]
    refute_empty result[:log]
  end

  def test_compile_log_ptx_matches_compile
    skip "NVRTC not available" unless NVRTC_OK
    ptx_direct = NvrtcRb.compile(PROBE_KERNEL, PROBE_OPTS)
    result      = NvrtcRb.compile_log(PROBE_KERNEL, PROBE_OPTS)
    # Both should produce PTX with the same kernel name
    assert_match(/probe/, result[:ptx])
    assert_match(/probe/, ptx_direct)
  end
end
