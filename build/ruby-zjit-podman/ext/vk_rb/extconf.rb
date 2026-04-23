require 'mkmf'

# vk_rb — Vulkan instance + physical device query extension
# Requires: vulkan-devel (Linux) or VulkanSDK (Win32)

# Linux: pkg-config vulkan path
if pkg_config('vulkan')
  # pkg_config sets $INCFLAGS and $libs automatically
else
  # Fallback: VULKAN_SDK env (Win32) or /usr (Linux system install)
  vk_base = ENV['VULKAN_SDK'] ||
             (File.exist?('/usr/include/vulkan/vulkan.h') ? '' : nil) ||
             abort('Cannot find Vulkan — install vulkan-devel or set VULKAN_SDK')

  unless vk_base.empty?
    $INCFLAGS  += " -I#{vk_base}/include"
    $LIBPATH    = ["#{vk_base}/Lib", "#{vk_base}/lib"] + $LIBPATH
  end

  unless find_header('vulkan/vulkan.h')
    abort "Cannot find vulkan/vulkan.h"
  end

  $LOCAL_LIBS += " -lvulkan-1" if RUBY_PLATFORM =~ /mswin|mingw/
  $LOCAL_LIBS += " -lvulkan"   unless RUBY_PLATFORM =~ /mswin|mingw/
end

create_makefile('vk_rb')
