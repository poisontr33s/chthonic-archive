#include "ruby.h"
#include <vulkan/vulkan.h>
#include <string.h>
#include <stdio.h>

/* VkRb.instance_version -> String "major.minor.patch" */
static VALUE rb_vk_instance_version(VALUE self) {
    uint32_t v = 0;
    if (vkEnumerateInstanceVersion(&v) != VK_SUCCESS)
        return rb_str_new_cstr("unavailable");
    char buf[32];
    snprintf(buf, sizeof(buf), "%u.%u.%u",
             VK_API_VERSION_MAJOR(v),
             VK_API_VERSION_MINOR(v),
             VK_API_VERSION_PATCH(v));
    return rb_str_new_cstr(buf);
}

/* Shared instance creation helper (no validation layers) */
static VkInstance make_probe_instance(void) {
    VkApplicationInfo app = {
        .sType              = VK_STRUCTURE_TYPE_APPLICATION_INFO,
        .pApplicationName   = "chthonic-ruby-zjit",
        .applicationVersion = VK_MAKE_VERSION(1, 0, 0),
        .pEngineName        = "chthonic",
        .engineVersion      = VK_MAKE_VERSION(1, 0, 0),
        .apiVersion         = VK_API_VERSION_1_3,
    };
    VkInstanceCreateInfo ci = {
        .sType            = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
        .pApplicationInfo = &app,
    };
    VkInstance inst = VK_NULL_HANDLE;
    vkCreateInstance(&ci, NULL, &inst);
    return inst;
}

/*
 * VkRb.physical_devices -> Array<Hash>
 * Each hash: {name:, device_type:, vendor_id:, device_id:, driver_version:, api_version:}
 */
static VALUE rb_vk_physical_devices(VALUE self) {
    VkInstance inst = make_probe_instance();
    if (inst == VK_NULL_HANDLE) return rb_ary_new();

    uint32_t count = 0;
    vkEnumeratePhysicalDevices(inst, &count, NULL);
    if (count == 0) {
        vkDestroyInstance(inst, NULL);
        return rb_ary_new();
    }

    VkPhysicalDevice *devs = ALLOCA_N(VkPhysicalDevice, count);
    vkEnumeratePhysicalDevices(inst, &count, devs);

    static const char *type_names[] = {
        "other", "integrated_gpu", "discrete_gpu", "virtual_gpu", "cpu"
    };

    VALUE result = rb_ary_new2(count);
    for (uint32_t i = 0; i < count; i++) {
        VkPhysicalDeviceProperties props;
        vkGetPhysicalDeviceProperties(devs[i], &props);

        VALUE h = rb_hash_new();
        rb_hash_aset(h, ID2SYM(rb_intern("name")),
                     rb_str_new_cstr(props.deviceName));
        int t = (int)props.deviceType;
        rb_hash_aset(h, ID2SYM(rb_intern("device_type")),
                     rb_str_new_cstr(t >= 0 && t <= 4 ? type_names[t] : "unknown"));
        rb_hash_aset(h, ID2SYM(rb_intern("vendor_id")),
                     UINT2NUM(props.vendorID));
        rb_hash_aset(h, ID2SYM(rb_intern("device_id")),
                     UINT2NUM(props.deviceID));
        rb_hash_aset(h, ID2SYM(rb_intern("driver_version")),
                     UINT2NUM(props.driverVersion));

        char api[32];
        snprintf(api, sizeof(api), "%u.%u.%u",
                 VK_API_VERSION_MAJOR(props.apiVersion),
                 VK_API_VERSION_MINOR(props.apiVersion),
                 VK_API_VERSION_PATCH(props.apiVersion));
        rb_hash_aset(h, ID2SYM(rb_intern("api_version")),
                     rb_str_new_cstr(api));

        rb_ary_push(result, h);
    }

    vkDestroyInstance(inst, NULL);
    return result;
}

/*
 * VkRb.instance_extensions -> Array<String>
 * Lists all available instance extension names.
 */
static VALUE rb_vk_instance_extensions(VALUE self) {
    uint32_t count = 0;
    vkEnumerateInstanceExtensionProperties(NULL, &count, NULL);
    if (count == 0) return rb_ary_new();

    VkExtensionProperties *exts = ALLOCA_N(VkExtensionProperties, count);
    vkEnumerateInstanceExtensionProperties(NULL, &count, exts);

    VALUE result = rb_ary_new2(count);
    for (uint32_t i = 0; i < count; i++)
        rb_ary_push(result, rb_str_new_cstr(exts[i].extensionName));
    return result;
}

/* VkRb.has_extension?(name) -> Boolean */
static VALUE rb_vk_has_extension(VALUE self, VALUE name) {
    const char *target = StringValueCStr(name);
    uint32_t count = 0;
    vkEnumerateInstanceExtensionProperties(NULL, &count, NULL);
    if (count == 0) return Qfalse;

    VkExtensionProperties *exts = ALLOCA_N(VkExtensionProperties, count);
    vkEnumerateInstanceExtensionProperties(NULL, &count, exts);

    for (uint32_t i = 0; i < count; i++)
        if (strcmp(exts[i].extensionName, target) == 0) return Qtrue;
    return Qfalse;
}

void Init_vk_rb(void) {
    VALUE mod = rb_define_module("VkRb");
    rb_define_singleton_method(mod, "instance_version",     rb_vk_instance_version,    0);
    rb_define_singleton_method(mod, "physical_devices",     rb_vk_physical_devices,    0);
    rb_define_singleton_method(mod, "instance_extensions",  rb_vk_instance_extensions, 0);
    rb_define_singleton_method(mod, "has_extension?",       rb_vk_has_extension,       1);
}
