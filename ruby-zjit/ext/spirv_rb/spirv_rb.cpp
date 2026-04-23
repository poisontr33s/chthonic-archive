/*
 * spirv_rb — SPIR-V reflection + transpilation via spirv-cross C API
 *
 * Methods:
 *   SpirvRb.disassemble(bytes, target: :glsl)  -> String
 *     Transpile SPIR-V binary to GLSL / MSL / HLSL source.
 *     target: :glsl (default), :msl, :hlsl
 *
 *   SpirvRb.reflect(bytes)                     -> Hash
 *     Extract shader resource layout without transpiling.
 *     Returns:
 *       stage_inputs:     [{name:, location:}]
 *       stage_outputs:    [{name:, location:}]
 *       uniform_buffers:  [{name:, set:, binding:}]
 *       storage_buffers:  [{name:, set:, binding:}]
 *       push_constants:   [{name:}]
 *       sampled_images:   [{name:, set:, binding:}]
 *       separate_images:  [{name:, set:, binding:}]
 *       separate_samplers:[{name:, set:, binding:}]
 *
 * bytes argument: Ruby String containing raw SPIR-V binary (uint32 words,
 * little-endian). Typically the contents of a .spv file.
 */

#include "ruby.h"
#include <spirv_cross/spirv_cross_c.h>
#include <string.h>
#include <stdint.h>

extern "C" {

/* ── internal: validate + extract words from Ruby String ─────────────────── */
static void extract_words(VALUE bytes_rb,
                           const SpvId **words_out,
                           size_t       *word_count_out) {
    Check_Type(bytes_rb, T_STRING);
    long len = RSTRING_LEN(bytes_rb);
    if (len < 20 || len % 4 != 0)
        rb_raise(rb_eArgError,
                 "SPIR-V binary must be at least 20 bytes and a multiple of 4 "
                 "(got %ld)", len);

    const uint8_t *raw = (const uint8_t *)RSTRING_PTR(bytes_rb);
    /* SPIR-V magic: 0x07230203 LE → bytes 03 02 23 07 */
    uint32_t magic;
    memcpy(&magic, raw, 4);
    if (magic != 0x07230203U)
        rb_raise(rb_eArgError,
                 "Not a SPIR-V binary — magic 0x%08X != 0x07230203", magic);

    *words_out      = (const SpvId *)raw;
    *word_count_out = (size_t)(len / 4);
}

/* ── internal: build spvc_compiler for a given backend ───────────────────── */
static spvc_compiler make_compiler(spvc_context ctx,
                                   const SpvId *words, size_t word_count,
                                   spvc_backend backend) {
    spvc_parsed_ir ir = NULL;
    spvc_result r = spvc_context_parse_spirv(ctx, words, word_count, &ir);
    if (r != SPVC_SUCCESS)
        rb_raise(rb_eRuntimeError, "spvc_context_parse_spirv: %s",
                 spvc_context_get_last_error_string(ctx));

    spvc_compiler compiler = NULL;
    r = spvc_context_create_compiler(ctx, backend, ir,
                                     SPVC_CAPTURE_MODE_TAKE_OWNERSHIP,
                                     &compiler);
    if (r != SPVC_SUCCESS)
        rb_raise(rb_eRuntimeError, "spvc_context_create_compiler: %s",
                 spvc_context_get_last_error_string(ctx));
    return compiler;
}

/* ── internal: build Array<Hash> for a resource list ─────────────────────── */
static VALUE resource_list_with_location(spvc_compiler compiler,
                                         const spvc_reflected_resource *list,
                                         size_t count) {
    VALUE ary = rb_ary_new2((long)count);
    for (size_t i = 0; i < count; i++) {
        VALUE h = rb_hash_new();
        rb_hash_aset(h, ID2SYM(rb_intern("name")),
                     rb_str_new_cstr(list[i].name ? list[i].name : ""));
        unsigned loc = spvc_compiler_get_decoration(
            compiler, list[i].id, SpvDecorationLocation);
        rb_hash_aset(h, ID2SYM(rb_intern("location")), UINT2NUM(loc));
        rb_ary_push(ary, h);
    }
    return ary;
}

static VALUE resource_list_with_binding(spvc_compiler compiler,
                                        const spvc_reflected_resource *list,
                                        size_t count) {
    VALUE ary = rb_ary_new2((long)count);
    for (size_t i = 0; i < count; i++) {
        VALUE h = rb_hash_new();
        rb_hash_aset(h, ID2SYM(rb_intern("name")),
                     rb_str_new_cstr(list[i].name ? list[i].name : ""));
        unsigned set = spvc_compiler_get_decoration(
            compiler, list[i].id, SpvDecorationDescriptorSet);
        unsigned binding = spvc_compiler_get_decoration(
            compiler, list[i].id, SpvDecorationBinding);
        rb_hash_aset(h, ID2SYM(rb_intern("set")),     UINT2NUM(set));
        rb_hash_aset(h, ID2SYM(rb_intern("binding")), UINT2NUM(binding));
        rb_ary_push(ary, h);
    }
    return ary;
}

static VALUE resource_list_push_constants(const spvc_reflected_resource *list,
                                          size_t count) {
    VALUE ary = rb_ary_new2((long)count);
    for (size_t i = 0; i < count; i++) {
        VALUE h = rb_hash_new();
        rb_hash_aset(h, ID2SYM(rb_intern("name")),
                     rb_str_new_cstr(list[i].name ? list[i].name : ""));
        rb_ary_push(ary, h);
    }
    return ary;
}

/* ── SpirvRb.disassemble(bytes, target: :glsl) -> String ─────────────────── */
static VALUE rb_spirv_disassemble(int argc, VALUE *argv, VALUE self) {
    VALUE bytes_rb, kwargs;
    rb_scan_args(argc, argv, "1:", &bytes_rb, &kwargs);

    spvc_backend backend = SPVC_BACKEND_GLSL;
    if (!NIL_P(kwargs)) {
        VALUE target = rb_hash_aref(kwargs, ID2SYM(rb_intern("target")));
        if (!NIL_P(target)) {
            ID tid = SYM2ID(target);
            if      (tid == rb_intern("glsl")) backend = SPVC_BACKEND_GLSL;
            else if (tid == rb_intern("msl"))  backend = SPVC_BACKEND_MSL;
            else if (tid == rb_intern("hlsl")) backend = SPVC_BACKEND_HLSL;
            else
                rb_raise(rb_eArgError,
                         "Unknown target: :%s — expected :glsl, :msl, or :hlsl",
                         rb_id2name(tid));
        }
    }

    const SpvId *words; size_t word_count;
    extract_words(bytes_rb, &words, &word_count);

    spvc_context ctx = NULL;
    spvc_context_create(&ctx);

    spvc_compiler compiler = make_compiler(ctx, words, word_count, backend);

    const char *source = NULL;
    spvc_result r = spvc_compiler_compile(compiler, &source);
    if (r != SPVC_SUCCESS) {
        const char *err = spvc_context_get_last_error_string(ctx);
        spvc_context_destroy(ctx);
        rb_raise(rb_eRuntimeError, "spvc_compiler_compile: %s", err);
    }

    VALUE result = rb_str_new_cstr(source);
    spvc_context_destroy(ctx);
    return result;
}

/* ── SpirvRb.reflect(bytes) -> Hash ──────────────────────────────────────── */
static VALUE rb_spirv_reflect(VALUE self, VALUE bytes_rb) {
    const SpvId *words; size_t word_count;
    extract_words(bytes_rb, &words, &word_count);

    spvc_context ctx = NULL;
    spvc_context_create(&ctx);

    /* SPVC_BACKEND_NONE for pure reflection without transpilation */
    spvc_compiler compiler = make_compiler(ctx, words, word_count,
                                           SPVC_BACKEND_NONE);

    spvc_resources resources = NULL;
    spvc_result r = spvc_compiler_create_shader_resources(compiler, &resources);
    if (r != SPVC_SUCCESS) {
        const char *err = spvc_context_get_last_error_string(ctx);
        spvc_context_destroy(ctx);
        rb_raise(rb_eRuntimeError, "create_shader_resources: %s", err);
    }

    /* helper macro to fetch a resource list */
#define FETCH(TYPE, VAR)                                                       \
    const spvc_reflected_resource *VAR##_list; size_t VAR##_count;            \
    spvc_resources_get_resource_list_for_type(                                 \
        resources, SPVC_RESOURCE_TYPE_##TYPE, &VAR##_list, &VAR##_count)

    FETCH(STAGE_INPUT,        inputs);
    FETCH(STAGE_OUTPUT,       outputs);
    FETCH(UNIFORM_BUFFER,     ubos);
    FETCH(STORAGE_BUFFER,     ssbos);
    FETCH(PUSH_CONSTANT,      push);
    FETCH(SAMPLED_IMAGE,      sampled);
    FETCH(SEPARATE_IMAGE,     sep_img);
    FETCH(SEPARATE_SAMPLERS,  sep_smp);
#undef FETCH

    VALUE h = rb_hash_new();
    rb_hash_aset(h, ID2SYM(rb_intern("stage_inputs")),
                 resource_list_with_location(compiler, inputs_list,    inputs_count));
    rb_hash_aset(h, ID2SYM(rb_intern("stage_outputs")),
                 resource_list_with_location(compiler, outputs_list,   outputs_count));
    rb_hash_aset(h, ID2SYM(rb_intern("uniform_buffers")),
                 resource_list_with_binding(compiler, ubos_list,       ubos_count));
    rb_hash_aset(h, ID2SYM(rb_intern("storage_buffers")),
                 resource_list_with_binding(compiler, ssbos_list,      ssbos_count));
    rb_hash_aset(h, ID2SYM(rb_intern("push_constants")),
                 resource_list_push_constants(push_list,               push_count));
    rb_hash_aset(h, ID2SYM(rb_intern("sampled_images")),
                 resource_list_with_binding(compiler, sampled_list,    sampled_count));
    rb_hash_aset(h, ID2SYM(rb_intern("separate_images")),
                 resource_list_with_binding(compiler, sep_img_list,    sep_img_count));
    rb_hash_aset(h, ID2SYM(rb_intern("separate_samplers")),
                 resource_list_with_binding(compiler, sep_smp_list,    sep_smp_count));

    spvc_context_destroy(ctx);
    return h;
}

void Init_spirv_rb(void) {
    VALUE mod = rb_define_module("SpirvRb");
    rb_define_singleton_method(mod, "disassemble", rb_spirv_disassemble, -1);
    rb_define_singleton_method(mod, "reflect",     rb_spirv_reflect,      1);
}

} /* extern "C" */
