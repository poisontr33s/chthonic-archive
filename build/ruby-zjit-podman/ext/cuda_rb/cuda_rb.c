#include "ruby.h"
#include <cuda_runtime_api.h>
#include <string.h>
#include <stdio.h>

/* CudaRb.device_count -> Integer */
static VALUE rb_cuda_device_count(VALUE self) {
    int count = 0;
    cudaError_t err = cudaGetDeviceCount(&count);
    if (err != cudaSuccess) return INT2NUM(0);
    return INT2NUM(count);
}

/* CudaRb.device_name(idx) -> String */
static VALUE rb_cuda_device_name(VALUE self, VALUE idx) {
    struct cudaDeviceProp prop;
    int n = NUM2INT(idx);
    cudaError_t err = cudaGetDeviceProperties(&prop, n);
    if (err != cudaSuccess) return rb_str_new_cstr("unavailable");
    return rb_str_new_cstr(prop.name);
}

/* CudaRb.device_compute_capability(idx) -> [major, minor] */
static VALUE rb_cuda_cc(VALUE self, VALUE idx) {
    struct cudaDeviceProp prop;
    int n = NUM2INT(idx);
    if (cudaGetDeviceProperties(&prop, n) != cudaSuccess)
        return rb_ary_new();
    VALUE ary = rb_ary_new2(2);
    rb_ary_push(ary, INT2NUM(prop.major));
    rb_ary_push(ary, INT2NUM(prop.minor));
    return ary;
}

/* CudaRb.driver_version -> Integer (e.g. 13020 = 13.2) */
static VALUE rb_cuda_driver_version(VALUE self) {
    int v = 0;
    cudaDriverGetVersion(&v);
    return INT2NUM(v);
}

/* CudaRb.runtime_version -> Integer */
static VALUE rb_cuda_runtime_version(VALUE self) {
    int v = 0;
    cudaRuntimeGetVersion(&v);
    return INT2NUM(v);
}

/*
 * CudaRb.devices -> Array<Hash>
 * Each hash: {name:, cc_major:, cc_minor:, total_memory:, sm_count:, clock_rate_khz:}
 */
static VALUE rb_cuda_devices(VALUE self) {
    int count = 0;
    if (cudaGetDeviceCount(&count) != cudaSuccess || count == 0)
        return rb_ary_new();

    VALUE result = rb_ary_new2(count);
    for (int i = 0; i < count; i++) {
        struct cudaDeviceProp prop;
        if (cudaGetDeviceProperties(&prop, i) != cudaSuccess) continue;
        VALUE h = rb_hash_new();
        rb_hash_aset(h, ID2SYM(rb_intern("name")),
                     rb_str_new_cstr(prop.name));
        rb_hash_aset(h, ID2SYM(rb_intern("cc_major")),
                     INT2NUM(prop.major));
        rb_hash_aset(h, ID2SYM(rb_intern("cc_minor")),
                     INT2NUM(prop.minor));
        rb_hash_aset(h, ID2SYM(rb_intern("total_memory")),
                     ULL2NUM((unsigned long long)prop.totalGlobalMem));
        rb_hash_aset(h, ID2SYM(rb_intern("sm_count")),
                     INT2NUM(prop.multiProcessorCount));
        rb_hash_aset(h, ID2SYM(rb_intern("clock_rate_khz")),
                     INT2NUM(prop.clockRate));
        rb_ary_push(result, h);
    }
    return result;
}

void Init_cuda_rb(void) {
    VALUE mod = rb_define_module("CudaRb");
    rb_define_singleton_method(mod, "device_count",            rb_cuda_device_count,   0);
    rb_define_singleton_method(mod, "device_name",             rb_cuda_device_name,    1);
    rb_define_singleton_method(mod, "device_compute_capability", rb_cuda_cc,           1);
    rb_define_singleton_method(mod, "driver_version",          rb_cuda_driver_version, 0);
    rb_define_singleton_method(mod, "runtime_version",         rb_cuda_runtime_version,0);
    rb_define_singleton_method(mod, "devices",                 rb_cuda_devices,        0);
}
