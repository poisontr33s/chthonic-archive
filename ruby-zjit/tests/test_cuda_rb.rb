# frozen_string_literal: true
require 'minitest/autorun'
require 'cuda_rb'

GPU_COUNT = begin; CudaRb.device_count; rescue => e; warn "cuda_rb init: #{e}"; 0; end

class TestCudaRb < Minitest::Test
  def test_driver_version_is_positive_integer
    v = CudaRb.driver_version
    assert_kind_of Integer, v
    assert_operator v, :>, 0, "driver_version should be > 0 (got #{v})"
  end

  def test_runtime_version_is_positive_integer
    v = CudaRb.runtime_version
    assert_kind_of Integer, v
    assert_operator v, :>, 0, "runtime_version should be > 0 (got #{v})"
  end

  def test_device_count_is_non_negative
    c = CudaRb.device_count
    assert_kind_of Integer, c
    assert_operator c, :>=, 0
  end

  def test_devices_returns_array
    devs = CudaRb.devices
    assert_kind_of Array, devs
    assert_equal GPU_COUNT, devs.size
  end

  def test_device_name_returns_nonempty_string
    skip "No CUDA GPU" if GPU_COUNT.zero?
    n = CudaRb.device_name(0)
    assert_kind_of String, n
    refute_empty n
  end

  def test_compute_capability_shape
    skip "No CUDA GPU" if GPU_COUNT.zero?
    cc = CudaRb.device_compute_capability(0)
    assert_kind_of Array, cc
    assert_equal 2, cc.size
    assert_operator cc[0], :>=, 3, "CC major should be >= 3 (Kepler+)"
    assert_operator cc[1], :>=, 0
  end

  def test_device_hash_keys
    skip "No CUDA GPU" if GPU_COUNT.zero?
    d = CudaRb.devices.first
    assert_kind_of Hash, d
    %i[name cc_major cc_minor total_memory sm_count clock_rate_khz].each do |k|
      assert d.key?(k), "Missing key :#{k} in devices hash"
    end
  end

  def test_device_hash_values_sane
    skip "No CUDA GPU" if GPU_COUNT.zero?
    d = CudaRb.devices.first
    refute_empty d[:name]
    assert_operator d[:cc_major], :>=, 3
    assert_operator d[:total_memory], :>, 0
    assert_operator d[:sm_count], :>, 0
    assert_operator d[:clock_rate_khz], :>, 0
  end

  def test_device_count_twice_stable
    assert_equal CudaRb.device_count, CudaRb.device_count,
      "device_count should be idempotent"
  end
end
