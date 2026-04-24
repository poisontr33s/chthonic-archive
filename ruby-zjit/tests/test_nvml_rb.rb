# frozen_string_literal: true
require 'minitest/autorun'
NVML_RB_AVAILABLE = begin; require 'nvml_rb'; true; rescue LoadError => e; warn "nvml_rb not built: #{e.message}"; false; end

NVML_COUNT = begin; NvmlRb.device_count; rescue => e; warn "nvml_rb init: #{e}"; 0; end

class TestNvmlRb < Minitest::Test
  def setup
    skip "nvml_rb extension not built — run build_win32.ps1" unless NVML_RB_AVAILABLE
  end
  def test_device_count_is_non_negative_integer
    c = NvmlRb.device_count
    assert_kind_of Integer, c
    assert_operator c, :>=, 0
  end

  def test_devices_returns_array
    devs = NvmlRb.devices
    assert_kind_of Array, devs
    assert_equal NVML_COUNT, devs.size
  end

  def test_version_returns_nonempty_string
    skip "NVML unavailable (no GPU or driver)" if NVML_COUNT.zero?
    v = NvmlRb.version
    assert_kind_of String, v
    refute_empty v
  end

  def test_version_looks_like_driver_version
    skip "NVML unavailable" if NVML_COUNT.zero?
    # Driver versions are like "596.21" or "560.28.03" (always contains a dot)
    assert_match(/\d+\.\d+/, NvmlRb.version,
      "version string '#{NvmlRb.version}' should look like a driver version (digits.digits)")
  end

  def test_device_hash_required_keys
    skip "No GPU" if NVML_COUNT.zero?
    d = NvmlRb.devices.first
    assert_kind_of Hash, d
    required = %i[name index total_memory_mib free_memory_mib
                  temperature_c fan_speed_pct
                  power_draw_w power_limit_w
                  sm_clock_mhz mem_clock_mhz
                  gpu_util_pct mem_util_pct
                  ecc_errors throttle_reasons]
    required.each { |k| assert d.key?(k), "Missing key :#{k} in devices hash" }
  end

  def test_device_name_nonempty
    skip "No GPU" if NVML_COUNT.zero?
    refute_empty NvmlRb.devices.first[:name]
  end

  def test_device_index_sequential
    skip "No GPU" if NVML_COUNT.zero?
    NvmlRb.devices.each_with_index do |d, i|
      assert_equal i, d[:index], "Device index should match array position"
    end
  end

  def test_device_memory_values_sane
    skip "No GPU" if NVML_COUNT.zero?
    d = NvmlRb.devices.first
    assert_operator d[:total_memory_mib], :>, 0, "total_memory_mib should be > 0"
    assert_operator d[:free_memory_mib], :>=, 0, "free_memory_mib should be >= 0"
    assert_operator d[:total_memory_mib], :>=, d[:free_memory_mib],
      "total_memory_mib should be >= free_memory_mib"
  end

  def test_device_temperature_reasonable
    skip "No GPU" if NVML_COUNT.zero?
    t = NvmlRb.devices.first[:temperature_c]
    assert_kind_of Integer, t
    assert_operator t, :>=, 0,   "temperature should be >= 0°C"
    assert_operator t, :<=, 120, "temperature should be <= 120°C (sanity check)"
  end

  def test_device_throttle_reasons_is_array_of_symbols
    skip "No GPU" if NVML_COUNT.zero?
    reasons = NvmlRb.devices.first[:throttle_reasons]
    assert_kind_of Array, reasons
    reasons.each { |r| assert_kind_of Symbol, r, "Throttle reason #{r.inspect} should be Symbol" }
  end

  def test_device_ecc_errors_is_hash_or_nil
    skip "No GPU" if NVML_COUNT.zero?
    ecc = NvmlRb.devices.first[:ecc_errors]
    if ecc
      assert_kind_of Hash, ecc
      assert ecc.key?(:sbe), "ecc_errors should have :sbe key"
      assert ecc.key?(:dbe), "ecc_errors should have :dbe key"
    end
    # nil is also valid — many consumer GPUs don't support ECC
  end

  def test_device_count_stable
    assert_equal NvmlRb.device_count, NvmlRb.device_count,
      "device_count should be idempotent"
  end
end
