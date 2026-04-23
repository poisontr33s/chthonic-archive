// trt_rb.cpp — TensorRT Ruby C++ extension
// NvInfer.h C++ API wrapped for Ruby. Compiled as C++17.
// Exposes: TrtRb.version, TrtRb.nvinfer_version, TrtRb.cuda_version,
//          TrtRb.create_logger, TrtRb.builder_available?

#include "ruby.h"
#include <NvInfer.h>
#include <cuda_runtime_api.h>
#include <cstdio>
#include <cstring>

// Minimal logger — required by TRT builder API
class SilentLogger : public nvinfer1::ILogger {
public:
    void log(Severity severity, const char* msg) noexcept override {
        (void)severity; (void)msg;
        // Suppress all TRT log output in the Ruby extension context.
        // The caller can implement their own logging if needed.
    }
};

static SilentLogger g_logger;

extern "C" {

/* TrtRb.version -> String "major.minor.patch.build" */
static VALUE rb_trt_version(VALUE self) {
    char buf[64];
    int v = NV_TENSORRT_VERSION;
    snprintf(buf, sizeof(buf), "%d.%d.%d",
             NV_TENSORRT_MAJOR,
             NV_TENSORRT_MINOR,
             NV_TENSORRT_PATCH);
    (void)v;
    return rb_str_new_cstr(buf);
}

/* TrtRb.nvinfer_version -> [major, minor, patch] */
static VALUE rb_trt_nvinfer_version(VALUE self) {
    VALUE ary = rb_ary_new2(3);
    rb_ary_push(ary, INT2NUM(NV_TENSORRT_MAJOR));
    rb_ary_push(ary, INT2NUM(NV_TENSORRT_MINOR));
    rb_ary_push(ary, INT2NUM(NV_TENSORRT_PATCH));
    return ary;
}

/* TrtRb.cuda_version -> Integer (from cudart at runtime) */
static VALUE rb_trt_cuda_version(VALUE self) {
    int v = 0;
    cudaRuntimeGetVersion(&v);
    return INT2NUM(v);
}

/*
 * TrtRb.builder_available? -> Boolean
 * Attempts to create and destroy a TRT builder.
 * Returns false in containers without GPU (expected in build env).
 */
static VALUE rb_trt_builder_available(VALUE self) {
    nvinfer1::IBuilder* builder = nullptr;
    builder = nvinfer1::createInferBuilder(g_logger);
    if (builder == nullptr) return Qfalse;
    builder->destroy();
    return Qtrue;
}

/*
 * TrtRb.network_flags -> Hash
 * Returns common network creation flags for reference.
 */
static VALUE rb_trt_network_flags(VALUE self) {
    VALUE h = rb_hash_new();
    rb_hash_aset(h, ID2SYM(rb_intern("explicit_batch")),
                 INT2NUM((int)nvinfer1::NetworkDefinitionCreationFlag::kEXPLICIT_BATCH));
    return h;
}

void Init_trt_rb(void) {
    VALUE mod = rb_define_module("TrtRb");
    rb_define_singleton_method(mod, "version",            rb_trt_version,           0);
    rb_define_singleton_method(mod, "nvinfer_version",    rb_trt_nvinfer_version,   0);
    rb_define_singleton_method(mod, "cuda_version",       rb_trt_cuda_version,      0);
    rb_define_singleton_method(mod, "builder_available?", rb_trt_builder_available, 0);
    rb_define_singleton_method(mod, "network_flags",      rb_trt_network_flags,     0);
}

} // extern "C"
