require 'mkmf'

# spirv_rb — SPIR-V reflection + transpilation via spirv-cross C API
# Header : spirv_cross/spirv_cross_c.h
# Library: libspirv-cross-c-shared (Vulkan SDK) or libspirv-cross-c (system)
#
# Header locations (checked in order):
#   1. VULKAN_SDK/include/spirv_cross/     (VulkanSDK install)
#   2. /usr/include/spirv_cross/           (system spirv-cross-devel, Fedora/Ubuntu)
#   3. pkg-config spirv-cross-c-shared     (some distros expose this)

# Prefer pkg-config first (cleanest)
have_pkg = pkg_config('spirv-cross-c-shared') || pkg_config('spirv-cross-c')

unless have_pkg
  vk_base = ENV['VULKAN_SDK'] || ''

  # Glob Vulkan SDK install if VULKAN_SDK not set (Win32 common location)
  if vk_base.empty? && RUBY_PLATFORM =~ /mswin|mingw/
    candidate = Dir.glob('C:/VulkanSDK/*').sort.last
    vk_base   = candidate if candidate && Dir.exist?(candidate)
  end

  inc_dirs = []
  lib_dirs = []

  unless vk_base.empty?
    inc_dirs << "#{vk_base}/include"
    lib_dirs << "#{vk_base}/lib"
    lib_dirs << "#{vk_base}/Lib"
  end
  # System header fallback
  inc_dirs << '/usr/include'
  inc_dirs << '/usr/local/include'

  $INCFLAGS += inc_dirs.map { |d| " -I#{d}" }.join
  $LIBPATH   = lib_dirs + $LIBPATH

  # Try both naming conventions used across distros / SDK versions
  linked = find_library('spirv-cross-c-shared', 'spvc_context_create', *lib_dirs) ||
           find_library('spirv-cross-c',         'spvc_context_create', *lib_dirs)
  abort "Cannot find libspirv-cross-c — install spirv-cross-devel or set VULKAN_SDK" unless linked

  unless find_header('spirv_cross/spirv_cross_c.h', *inc_dirs)
    abort "Cannot find spirv_cross/spirv_cross_c.h — check spirv-cross-devel install"
  end
end

# spirv-cross C API header requires C++ linkage internally; build as C++
$CXXFLAGS += ' -std=c++17'

create_makefile('spirv_rb')
