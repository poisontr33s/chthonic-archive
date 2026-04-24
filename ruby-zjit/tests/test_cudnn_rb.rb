# frozen_string_literal: true
require 'minitest/autorun'
CUDNN_RB_AVAILABLE = begin; require 'cudnn_rb'; true; rescue LoadError => e; warn "cudnn_rb not built: #{e.message}"; false; end

CUDNN_AVAIL = begin; CudnnRb.available?; rescue => e; warn "cudnn_rb init: #{e}"; false; end

class TestCudnnRb < Minitest::Test
  def setup
    skip "cudnn_rb extension not built — run build_win32.ps1" unless CUDNN_RB_AVAILABLE
  end
  def test_version_returns_triple_array
    v = CudnnRb.version
    assert_kind_of Array, v
    assert_equal 3, v.size, "version should be [major, minor, patch]"
    v.each { |n| assert_kind_of Integer, n }
  end

  def test_version_major_sane
    maj = CudnnRb.version[0]
    # cuDNN v8 and v9 are current; WIN32_PROFILE has v9.20
    assert_operator maj, :>=, 8, "cuDNN major should be >= 8"
  end

  def test_cuda_version_is_non_negative_integer
    v = CudnnRb.cuda_version
    assert_kind_of Integer, v
    assert_operator v, :>=, 0
  end

  def test_available_returns_boolean
    result = CudnnRb.available?
    assert_includes [true, false], result
  end

  def test_status_string_for_zero_is_string
    s = CudnnRb.status_string(0)
    assert_kind_of String, s
    refute_empty s
  end

  def test_status_string_success_code
    # CUDNN_STATUS_SUCCESS == 0
    s = CudnnRb.status_string(0)
    assert_match(/success/i, s, "status 0 should be 'success'")
  end

  def test_status_string_error_code
    # CUDNN_STATUS_NOT_INITIALIZED == 1
    s = CudnnRb.status_string(1)
    assert_kind_of String, s
    refute_empty s
  end

  def test_available_true_with_handle
    skip "cuDNN handle unavailable (no GPU or no cuDNN libs)" unless CUDNN_AVAIL
    assert CudnnRb.available?
  end

  def test_cuda_version_positive_when_available
    skip "cuDNN handle unavailable" unless CUDNN_AVAIL
    assert_operator CudnnRb.cuda_version, :>, 0
  end

  def test_version_triple_nonzero_when_available
    skip "cuDNN handle unavailable" unless CUDNN_AVAIL
    v = CudnnRb.version
    assert v.any? { |n| n > 0 }, "version triple should have at least one non-zero component"
  end
end
