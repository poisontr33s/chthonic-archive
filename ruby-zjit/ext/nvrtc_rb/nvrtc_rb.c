#include "ruby.h"
#include <nvrtc.h>
#include <stdlib.h>
#include <string.h>

/*
 * NvrtcRb — NVIDIA Runtime Compilation (NVRTC)
 *
 * Compile CUDA C/C++ source strings to PTX at runtime — no nvcc binary needed.
 * The PTX can be loaded into a CUmodule via the CUDA Driver API.
 *
 * Methods:
 *   NvrtcRb.version                       -> [major, minor]
 *   NvrtcRb.compile(src, opts=[])         -> ptx_string
 *   NvrtcRb.compile_log(src, opts=[])     -> {ptx:, log:}   (always returns log)
 *
 * Raises RuntimeError with the NVRTC program log on compile failure.
 *
 * Example:
 *   ptx = NvrtcRb.compile(<<~CUDA, ["--gpu-architecture=sm_89"])
 *     extern "C" __global__ void add(float *a, float *b, float *c, int n) {
 *       int i = blockIdx.x * blockDim.x + threadIdx.x;
 *       if (i < n) c[i] = a[i] + b[i];
 *     }
 *   CUDA
 */

/* ── helpers ─────────────────────────────────────────────────────────────── */

static void build_opts(VALUE opts_rb, int *num_opts_out, const char ***opts_out) {
    if (NIL_P(opts_rb) || RARRAY_LEN(opts_rb) == 0) {
        *num_opts_out = 0;
        *opts_out     = NULL;
        return;
    }
    Check_Type(opts_rb, T_ARRAY);
    int n = (int)RARRAY_LEN(opts_rb);
    const char **arr = (const char **)xmalloc(sizeof(const char *) * n);
    for (int i = 0; i < n; i++)
        arr[i] = StringValueCStr(rb_ary_entry(opts_rb, i));
    *num_opts_out = n;
    *opts_out     = arr;
}

/* compile inner — returns {ptx VALUE, log VALUE or Qnil} via out-params */
static nvrtcResult do_compile(const char *src,
                              int num_opts, const char **opts,
                              VALUE *ptx_out, VALUE *log_out) {
    nvrtcProgram prog;
    nvrtcResult r = nvrtcCreateProgram(&prog, src, "kernel.cu", 0, NULL, NULL);
    if (r != NVRTC_SUCCESS) {
        *ptx_out = Qnil;
        *log_out = rb_str_new_cstr(nvrtcGetErrorString(r));
        return r;
    }

    r = nvrtcCompileProgram(prog, num_opts, opts);

    /* always collect the log */
    size_t log_size = 0;
    nvrtcGetProgramLogSize(prog, &log_size);
    char *log_buf = (char *)xmalloc(log_size + 1);
    nvrtcGetProgramLog(prog, log_buf);
    log_buf[log_size] = '\0';
    *log_out = rb_str_new_cstr(log_buf);
    xfree(log_buf);

    if (r != NVRTC_SUCCESS) {
        nvrtcDestroyProgram(&prog);
        *ptx_out = Qnil;
        return r;
    }

    size_t ptx_size = 0;
    nvrtcGetPTXSize(prog, &ptx_size);
    char *ptx_buf = (char *)xmalloc(ptx_size + 1);
    nvrtcGetPTX(prog, ptx_buf);
    ptx_buf[ptx_size] = '\0';
    *ptx_out = rb_str_new_cstr(ptx_buf);
    xfree(ptx_buf);

    nvrtcDestroyProgram(&prog);
    return NVRTC_SUCCESS;
}

/* ── NvrtcRb.version -> [major, minor] ───────────────────────────────────── */
static VALUE rb_nvrtc_version(VALUE self) {
    int major = 0, minor = 0;
    nvrtcVersion(&major, &minor);
    VALUE ary = rb_ary_new2(2);
    rb_ary_push(ary, INT2NUM(major));
    rb_ary_push(ary, INT2NUM(minor));
    return ary;
}

/* ── NvrtcRb.compile(src, opts=[]) -> ptx_string ────────────────────────── */
static VALUE rb_nvrtc_compile(int argc, VALUE *argv, VALUE self) {
    VALUE src_rb, opts_rb;
    rb_scan_args(argc, argv, "11", &src_rb, &opts_rb);

    int num_opts = 0;
    const char **opts = NULL;
    build_opts(opts_rb, &num_opts, &opts);

    const char *src = StringValueCStr(src_rb);
    VALUE ptx, log;
    nvrtcResult r = do_compile(src, num_opts, opts, &ptx, &log);
    xfree(opts);

    if (r != NVRTC_SUCCESS) {
        rb_raise(rb_eRuntimeError, "NVRTC compilation failed [%s]:\n%s",
                 nvrtcGetErrorString(r), StringValueCStr(log));
    }
    return ptx;
}

/*
 * NvrtcRb.compile_log(src, opts=[]) -> {ptx: String|nil, log: String, success: Boolean}
 * Always returns the compilation log — useful for warnings even on success.
 */
static VALUE rb_nvrtc_compile_log(int argc, VALUE *argv, VALUE self) {
    VALUE src_rb, opts_rb;
    rb_scan_args(argc, argv, "11", &src_rb, &opts_rb);

    int num_opts = 0;
    const char **opts = NULL;
    build_opts(opts_rb, &num_opts, &opts);

    const char *src = StringValueCStr(src_rb);
    VALUE ptx, log;
    nvrtcResult r = do_compile(src, num_opts, opts, &ptx, &log);
    xfree(opts);

    VALUE h = rb_hash_new();
    rb_hash_aset(h, ID2SYM(rb_intern("ptx")),     ptx);
    rb_hash_aset(h, ID2SYM(rb_intern("log")),     log);
    rb_hash_aset(h, ID2SYM(rb_intern("success")), r == NVRTC_SUCCESS ? Qtrue : Qfalse);
    return h;
}

void Init_nvrtc_rb(void) {
    VALUE mod = rb_define_module("NvrtcRb");
    rb_define_singleton_method(mod, "version",     rb_nvrtc_version,     0);
    rb_define_singleton_method(mod, "compile",     rb_nvrtc_compile,    -1);
    rb_define_singleton_method(mod, "compile_log", rb_nvrtc_compile_log,-1);
}
