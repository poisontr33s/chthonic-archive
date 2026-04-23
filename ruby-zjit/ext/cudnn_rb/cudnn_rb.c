#include "ruby.h"
#include <cudnn.h>
#include <string.h>

/*
 * CudnnRb — cuDNN version + handle availability probe
 *
 * Methods:
 *   CudnnRb.version         -> [major, minor, patch]
 *   CudnnRb.cuda_version    -> Integer  (cuDNN's linked CUDA runtime version)
 *   CudnnRb.available?      -> Boolean  (creates + destroys a handle)
 *   CudnnRb.status_string(n)-> String   (human-readable cudnnStatus_t)
 */

/* CudnnRb.version -> [major, minor, patch] */
static VALUE rb_cudnn_version(VALUE self) {
    size_t ver = cudnnGetVersion();
    VALUE ary = rb_ary_new2(3);
    rb_ary_push(ary, INT2NUM((int)(ver / 1000)));
    rb_ary_push(ary, INT2NUM((int)((ver / 100) % 10)));
    rb_ary_push(ary, INT2NUM((int)(ver % 100)));
    return ary;
}

/* CudnnRb.cuda_version -> Integer (e.g. 13020 = CUDA 13.2) */
static VALUE rb_cudnn_cuda_version(VALUE self) {
    return INT2NUM((int)cudnnGetCudartVersion());
}

/*
 * CudnnRb.available? -> Boolean
 * Creates a cudnnHandle_t, destroys it, returns true on success.
 * Returns false if no GPU or CUDA context is unavailable.
 */
static VALUE rb_cudnn_available_p(VALUE self) {
    cudnnHandle_t handle;
    cudnnStatus_t status = cudnnCreate(&handle);
    if (status != CUDNN_STATUS_SUCCESS) return Qfalse;
    cudnnDestroy(handle);
    return Qtrue;
}

/* CudnnRb.status_string(status_int) -> String */
static VALUE rb_cudnn_status_string(VALUE self, VALUE code) {
    return rb_str_new_cstr(cudnnGetErrorString((cudnnStatus_t)NUM2INT(code)));
}

void Init_cudnn_rb(void) {
    VALUE mod = rb_define_module("CudnnRb");
    rb_define_singleton_method(mod, "version",        rb_cudnn_version,        0);
    rb_define_singleton_method(mod, "cuda_version",   rb_cudnn_cuda_version,   0);
    rb_define_singleton_method(mod, "available?",     rb_cudnn_available_p,    0);
    rb_define_singleton_method(mod, "status_string",  rb_cudnn_status_string,  1);
}
