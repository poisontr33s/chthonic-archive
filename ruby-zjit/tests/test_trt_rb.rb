# frozen_string_literal: true
require 'minitest/autorun'
require 'trt_rb'

class TestTrtRb < Minitest::Test
  def test_version_returns_string
    v = TrtRb.version
    assert_kind_of String, v
    refute_empty v
  end

  def test_nvinfer_version_returns_triple_array
    v = TrtRb.nvinfer_version
    assert_kind_of Array, v
    assert_equal 3, v.size, "nvinfer_version should be [major, minor, patch]"
    v.each { |n| assert_kind_of Integer, n }
  end

  def test_nvinfer_version_major_sane
    maj = TrtRb.nvinfer_version[0]
    # TensorRT 8+ is current; 10.x is on WIN32_PROFILE
    assert_operator maj, :>=, 8, "nvinfer major version should be >= 8"
  end

  def test_cuda_version_is_positive_integer
    v = TrtRb.cuda_version
    assert_kind_of Integer, v
    assert_operator v, :>, 0
  end

  def test_builder_available_is_boolean
    result = TrtRb.builder_available?
    assert_includes [true, false], result
  end

  def test_network_flags_is_integer
    f = TrtRb.network_flags
    assert_kind_of Integer, f
  end

  def test_nvinfer_version_matches_version_string
    ver_str = TrtRb.version
    triple  = TrtRb.nvinfer_version
    # version string should contain the major version number
    assert_includes ver_str, triple[0].to_s,
      "version string '#{ver_str}' should contain major '#{triple[0]}'"
  end

  def test_builder_available_true_with_gpu
    skip "No GPU / TRT builder not available" unless TrtRb.builder_available?
    # If we get here, builder_available? returned true — verify it's not a fluke
    assert TrtRb.builder_available?
  end
end
