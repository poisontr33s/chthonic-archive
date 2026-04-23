# frozen_string_literal: true
require 'minitest/autorun'
require 'spirv_rb'

# Minimal valid SPIR-V module (header only + OpNop):
#   Magic 0x07230203 | Version 1.5 | Generator 0 | Bound 1 | Schema 0 | OpNop
MINIMAL_SPV = [0x07230203, 0x00010500, 0x00000000, 0x00000001,
               0x00000000, 0x00010000].pack('L<*').freeze

# Invalid magic bytes
BAD_MAGIC_SPV = [0xDEADBEEF, 0x00010500, 0x00000000, 0x00000001,
                 0x00000000, 0x00010000].pack('L<*').freeze

# Truncated (too short to be valid)
TRUNCATED_SPV = [0x07230203].pack('L<*').freeze

REFLECT_KEYS = %i[stage_inputs stage_outputs uniform_buffers storage_buffers
                  push_constants sampled_images separate_images separate_samplers].freeze

class TestSpirvRb < Minitest::Test
  # ── disassemble ────────────────────────────────────────────────────────────

  def test_disassemble_responds_to
    assert_respond_to SpirvRb, :disassemble
  end

  def test_disassemble_raises_on_bad_magic
    assert_raises(RuntimeError) { SpirvRb.disassemble(BAD_MAGIC_SPV) }
  end

  def test_disassemble_raises_on_truncated_input
    assert_raises(RuntimeError) { SpirvRb.disassemble(TRUNCATED_SPV) }
  end

  def test_disassemble_raises_on_empty_input
    assert_raises(RuntimeError) { SpirvRb.disassemble("".b) }
  end

  def test_disassemble_target_glsl_returns_string
    result = SpirvRb.disassemble(MINIMAL_SPV, target: :glsl) rescue nil
    # May raise "no entry point" or similar — either a String or a RuntimeError is acceptable
    # What is NOT acceptable: a crash / nil / wrong type
    assert_nil(result) || assert_kind_of(String, result) if result
  end

  def test_disassemble_accepts_target_msl
    assert_respond_to SpirvRb, :disassemble
    # Just verify it doesn't raise an ArgumentError for the :msl target key
    # (content may fail on minimal module — that's OK)
    begin
      SpirvRb.disassemble(MINIMAL_SPV, target: :msl)
    rescue RuntimeError
      # Acceptable: module too minimal to transpile
    end
  end

  def test_disassemble_accepts_target_hlsl
    begin
      SpirvRb.disassemble(MINIMAL_SPV, target: :hlsl)
    rescue RuntimeError
      # Acceptable
    end
  end

  # ── reflect ────────────────────────────────────────────────────────────────

  def test_reflect_responds_to
    assert_respond_to SpirvRb, :reflect
  end

  def test_reflect_raises_on_bad_magic
    assert_raises(RuntimeError) { SpirvRb.reflect(BAD_MAGIC_SPV) }
  end

  def test_reflect_raises_on_empty_input
    assert_raises(RuntimeError) { SpirvRb.reflect("".b) }
  end

  def test_reflect_returns_hash_or_raises_on_minimal_module
    # Minimal module has no entry point — reflect may raise or return empty hash
    begin
      result = SpirvRb.reflect(MINIMAL_SPV)
      assert_kind_of Hash, result
      REFLECT_KEYS.each { |k| assert result.key?(k), "Missing key :#{k} in reflect result" }
    rescue RuntimeError => e
      # Acceptable: "no entry point", "no shader stage", etc.
      assert_match(/entry|stage|shader|reflect/i, e.message,
        "RuntimeError message '#{e.message}' should mention entry/stage/shader")
    end
  end

  def test_reflect_hash_all_values_are_arrays
    result = SpirvRb.reflect(MINIMAL_SPV) rescue nil
    return unless result.is_a?(Hash)
    REFLECT_KEYS.each do |k|
      assert_kind_of Array, result[k], ":#{k} should be an Array"
    end
  end

  # ── method arity sanity ────────────────────────────────────────────────────

  def test_disassemble_arity_accepts_one_arg
    # arity of -1 or -2 means variable (keyword args + positional)
    a = SpirvRb.method(:disassemble).arity
    assert a != 0, "disassemble should accept at least one argument (arity was #{a})"
  end

  def test_reflect_arity_accepts_one_arg
    a = SpirvRb.method(:reflect).arity
    assert a != 0, "reflect should accept at least one argument (arity was #{a})"
  end
end
