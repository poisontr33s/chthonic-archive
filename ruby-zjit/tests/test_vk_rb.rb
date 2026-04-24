# frozen_string_literal: true
require 'minitest/autorun'
VK_RB_AVAILABLE = begin; require 'vk_rb'; true; rescue LoadError => e; warn "vk_rb not built: #{e.message}"; false; end

VK_DEVS = begin; VkRb.physical_devices; rescue => e; warn "vk_rb init: #{e}"; []; end

class TestVkRb < Minitest::Test
  def setup
    skip "vk_rb extension not built — run build_win32.ps1" unless VK_RB_AVAILABLE
  end
  def test_instance_version_is_not_nil
    v = VkRb.instance_version
    refute_nil v
  end

  def test_instance_extensions_returns_array
    exts = VkRb.instance_extensions
    assert_kind_of Array, exts
    assert exts.all?(String), "instance_extensions should be Array<String>"
  end

  def test_has_extension_returns_boolean
    # Any result is valid — just must be true or false
    result = VkRb.has_extension?("VK_KHR_surface")
    assert_includes [true, false], result
  end

  def test_has_extension_false_for_nonsense
    result = VkRb.has_extension?("VK_MADE_UP_NOT_REAL_XYZ_12345")
    assert_equal false, result
  end

  def test_physical_devices_returns_array
    devs = VkRb.physical_devices
    assert_kind_of Array, devs
  end

  def test_physical_device_hash_keys
    skip "No Vulkan device" if VK_DEVS.empty?
    d = VK_DEVS.first
    assert_kind_of Hash, d
    assert d.key?(:name),        "Missing :name"
    assert d.key?(:device_type), "Missing :device_type"
    assert d.key?(:api_version), "Missing :api_version"
  end

  def test_physical_device_name_nonempty
    skip "No Vulkan device" if VK_DEVS.empty?
    refute_empty VK_DEVS.first[:name]
  end

  def test_instance_extensions_nonempty_with_device
    skip "No Vulkan device" if VK_DEVS.empty?
    exts = VkRb.instance_extensions
    refute_empty exts, "Instance extensions should be non-empty with a Vulkan device present"
  end

  def test_surface_extension_present_with_device
    skip "No Vulkan device" if VK_DEVS.empty?
    # RTX 4090 / any GPU with display: VK_KHR_surface must be present
    assert VkRb.has_extension?("VK_KHR_surface"),
      "VK_KHR_surface expected with physical GPU"
  end
end
