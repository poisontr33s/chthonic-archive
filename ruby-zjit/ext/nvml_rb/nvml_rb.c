#include "ruby.h"
#include <nvml.h>
#include <string.h>
#include <stdio.h>

/*
 * NvmlRb — NVIDIA Management Library probe
 *
 * Methods:
 *   NvmlRb.version          -> String   (driver version, e.g. "596.21")
 *   NvmlRb.device_count     -> Integer
 *   NvmlRb.devices          -> Array<Hash>  (full telemetry per device)
 *
 * devices Hash keys (all values are -1 / nil on query failure):
 *   name              String
 *   index             Integer
 *   total_memory_mib  Integer   — total VRAM in MiB
 *   free_memory_mib   Integer   — free VRAM in MiB
 *   temperature_c     Integer   — GPU core temp in Celsius
 *   fan_speed_pct     Integer   — 0..100, -1 if N/A (passive cooling)
 *   power_draw_w      Float     — current power draw in Watts
 *   power_limit_w     Float     — enforced power cap in Watts
 *   sm_clock_mhz      Integer   — current SM clock
 *   mem_clock_mhz     Integer   — current memory clock
 *   gpu_util_pct      Integer   — GPU utilization %
 *   mem_util_pct      Integer   — memory controller utilization %
 *   ecc_errors        Hash/nil  — {sbe: Integer, dbe: Integer} or nil
 *   throttle_reasons  Array<Symbol>
 */

/* ── Init / shutdown ──────────────────────────────────────────────────────── */
static int nvml_up = 0;

static int ensure_nvml(void) {
    if (nvml_up) return 1;
    nvmlReturn_t r = nvmlInit_v2();
    nvml_up = (r == NVML_SUCCESS);
    return nvml_up;
}

/* ── Throttle reasons ─────────────────────────────────────────────────────── */
static VALUE build_throttle_reasons(unsigned long long mask) {
    static const struct { unsigned long long bit; const char *sym; } BITS[] = {
        { 0x0000000000000001ULL, "gpu_idle"       },
        { 0x0000000000000002ULL, "app_clocks"     },
        { 0x0000000000000004ULL, "sw_power_cap"   },
        { 0x0000000000000008ULL, "hw_slowdown"    },
        { 0x0000000000000010ULL, "sync_boost"     },
        { 0x0000000000000020ULL, "sw_thermal"     },
        { 0x0000000000000040ULL, "hw_thermal"     },
        { 0x0000000000000080ULL, "hw_power_brake" },
        { 0x0000000000000100ULL, "display_clocks" },
        { 0, NULL }
    };
    VALUE ary = rb_ary_new();
    for (int i = 0; BITS[i].sym; i++) {
        if (mask & BITS[i].bit)
            rb_ary_push(ary, ID2SYM(rb_intern(BITS[i].sym)));
    }
    return ary;
}

/* ── NvmlRb.version -> String ────────────────────────────────────────────── */
static VALUE rb_nvml_version(VALUE self) {
    char buf[NVML_SYSTEM_DRIVER_VERSION_BUFFER_SIZE];
    if (!ensure_nvml()) return rb_str_new_cstr("unavailable");
    if (nvmlSystemGetDriverVersion(buf, sizeof(buf)) != NVML_SUCCESS)
        return rb_str_new_cstr("unavailable");
    return rb_str_new_cstr(buf);
}

/* ── NvmlRb.device_count -> Integer ─────────────────────────────────────── */
static VALUE rb_nvml_device_count(VALUE self) {
    unsigned int count = 0;
    if (!ensure_nvml()) return INT2NUM(0);
    nvmlDeviceGetCount_v2(&count);
    return UINT2NUM(count);
}

/* ── NvmlRb.devices -> Array<Hash> ──────────────────────────────────────── */
static VALUE rb_nvml_devices(VALUE self) {
    if (!ensure_nvml()) return rb_ary_new();

    unsigned int count = 0;
    nvmlDeviceGetCount_v2(&count);
    VALUE result = rb_ary_new2(count);

    for (unsigned int i = 0; i < count; i++) {
        nvmlDevice_t dev;
        if (nvmlDeviceGetHandleByIndex_v2(i, &dev) != NVML_SUCCESS) continue;

        VALUE h = rb_hash_new();

        /* name */
        char name[NVML_DEVICE_NAME_BUFFER_SIZE];
        if (nvmlDeviceGetName(dev, name, sizeof(name)) == NVML_SUCCESS)
            rb_hash_aset(h, ID2SYM(rb_intern("name")), rb_str_new_cstr(name));
        else
            rb_hash_aset(h, ID2SYM(rb_intern("name")), rb_str_new_cstr("unknown"));

        rb_hash_aset(h, ID2SYM(rb_intern("index")), UINT2NUM(i));

        /* memory */
        nvmlMemory_t mem;
        if (nvmlDeviceGetMemoryInfo(dev, &mem) == NVML_SUCCESS) {
            rb_hash_aset(h, ID2SYM(rb_intern("total_memory_mib")),
                         ULL2NUM(mem.total >> 20));
            rb_hash_aset(h, ID2SYM(rb_intern("free_memory_mib")),
                         ULL2NUM(mem.free >> 20));
        } else {
            rb_hash_aset(h, ID2SYM(rb_intern("total_memory_mib")), INT2NUM(-1));
            rb_hash_aset(h, ID2SYM(rb_intern("free_memory_mib")),  INT2NUM(-1));
        }

        /* temperature */
        unsigned int temp = 0;
        int temp_val = (nvmlDeviceGetTemperature(dev, NVML_TEMPERATURE_GPU, &temp)
                        == NVML_SUCCESS) ? (int)temp : -1;
        rb_hash_aset(h, ID2SYM(rb_intern("temperature_c")), INT2NUM(temp_val));

        /* fan speed */
        unsigned int fan = 0;
        int fan_val = (nvmlDeviceGetFanSpeed(dev, &fan) == NVML_SUCCESS)
                      ? (int)fan : -1;
        rb_hash_aset(h, ID2SYM(rb_intern("fan_speed_pct")), INT2NUM(fan_val));

        /* power draw */
        unsigned int pmw = 0;
        if (nvmlDeviceGetPowerUsage(dev, &pmw) == NVML_SUCCESS)
            rb_hash_aset(h, ID2SYM(rb_intern("power_draw_w")),
                         rb_float_new(pmw / 1000.0));
        else
            rb_hash_aset(h, ID2SYM(rb_intern("power_draw_w")), Qnil);

        /* power limit */
        unsigned int plim = 0;
        if (nvmlDeviceGetEnforcedPowerLimit(dev, &plim) == NVML_SUCCESS)
            rb_hash_aset(h, ID2SYM(rb_intern("power_limit_w")),
                         rb_float_new(plim / 1000.0));
        else
            rb_hash_aset(h, ID2SYM(rb_intern("power_limit_w")), Qnil);

        /* SM clock */
        unsigned int sm_clk = 0;
        int sm_val = (nvmlDeviceGetClockInfo(dev, NVML_CLOCK_SM, &sm_clk)
                      == NVML_SUCCESS) ? (int)sm_clk : -1;
        rb_hash_aset(h, ID2SYM(rb_intern("sm_clock_mhz")), INT2NUM(sm_val));

        /* memory clock */
        unsigned int mem_clk = 0;
        int mem_val = (nvmlDeviceGetClockInfo(dev, NVML_CLOCK_MEM, &mem_clk)
                       == NVML_SUCCESS) ? (int)mem_clk : -1;
        rb_hash_aset(h, ID2SYM(rb_intern("mem_clock_mhz")), INT2NUM(mem_val));

        /* utilization */
        nvmlUtilization_t util;
        if (nvmlDeviceGetUtilizationRates(dev, &util) == NVML_SUCCESS) {
            rb_hash_aset(h, ID2SYM(rb_intern("gpu_util_pct")),
                         UINT2NUM(util.gpu));
            rb_hash_aset(h, ID2SYM(rb_intern("mem_util_pct")),
                         UINT2NUM(util.memory));
        } else {
            rb_hash_aset(h, ID2SYM(rb_intern("gpu_util_pct")), INT2NUM(-1));
            rb_hash_aset(h, ID2SYM(rb_intern("mem_util_pct")), INT2NUM(-1));
        }

        /* ECC errors (only on ECC-enabled cards) */
        unsigned long long ecc_sbe = 0, ecc_dbe = 0;
        nvmlReturn_t rsbe = nvmlDeviceGetTotalEccErrors(
            dev, NVML_MEMORY_ERROR_TYPE_UNCORRECTED, NVML_VOLATILE_ECC, &ecc_dbe);
        nvmlReturn_t rdbe = nvmlDeviceGetTotalEccErrors(
            dev, NVML_MEMORY_ERROR_TYPE_CORRECTED,   NVML_VOLATILE_ECC, &ecc_sbe);
        if (rsbe == NVML_SUCCESS || rdbe == NVML_SUCCESS) {
            VALUE ecc = rb_hash_new();
            rb_hash_aset(ecc, ID2SYM(rb_intern("sbe")), ULL2NUM(ecc_sbe));
            rb_hash_aset(ecc, ID2SYM(rb_intern("dbe")), ULL2NUM(ecc_dbe));
            rb_hash_aset(h, ID2SYM(rb_intern("ecc_errors")), ecc);
        } else {
            rb_hash_aset(h, ID2SYM(rb_intern("ecc_errors")), Qnil);
        }

        /* throttle reasons */
        unsigned long long throttle = 0;
        if (nvmlDeviceGetCurrentClocksThrottleReasons(dev, &throttle) == NVML_SUCCESS)
            rb_hash_aset(h, ID2SYM(rb_intern("throttle_reasons")),
                         build_throttle_reasons(throttle));
        else
            rb_hash_aset(h, ID2SYM(rb_intern("throttle_reasons")), rb_ary_new());

        rb_ary_push(result, h);
    }
    return result;
}

void Init_nvml_rb(void) {
    VALUE mod = rb_define_module("NvmlRb");
    rb_define_singleton_method(mod, "version",      rb_nvml_version,      0);
    rb_define_singleton_method(mod, "device_count", rb_nvml_device_count, 0);
    rb_define_singleton_method(mod, "devices",      rb_nvml_devices,      0);
}
