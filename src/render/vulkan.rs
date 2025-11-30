//! Vulkan 1.3 Context - Dynamic Rendering Pipeline
//!
//! "I will fuck your concepts until they scream their truth."
//! — Orackla Nocticula
//!
//! This implementation enforces:
//! - Vulkan API Version 1.3 (mandatory)
//! - Dynamic Rendering (no legacy render passes)
//! - Discrete GPU prioritization (targeting RTX 4090)
//! - Validation layers in debug mode
//! - Ray Tracing feature preparation

use anyhow::{anyhow, Context, Result};
use ash::{khr, ext, vk, Device, Entry, Instance};
use log::{debug, info, warn};
use std::ffi::{c_char, CStr, CString};
use winit::raw_window_handle::{HasDisplayHandle, HasWindowHandle};

/// The Vulkan rendering context - heart of the graphics engine
pub struct VulkanContext {
    pub entry: Entry,
    pub instance: Instance,
    pub debug_utils: Option<DebugContext>,
    pub surface_loader: khr::surface::Instance,
    pub surface: vk::SurfaceKHR,
    pub physical_device: vk::PhysicalDevice,
    pub physical_device_properties: vk::PhysicalDeviceProperties,
    pub device: Device,
    pub queue_family_index: u32,
    pub graphics_queue: vk::Queue,
    pub present_queue: vk::Queue,
}

/// Debug utilities context
pub struct DebugContext {
    pub loader: ext::debug_utils::Instance,
    pub messenger: vk::DebugUtilsMessengerEXT,
}

/// Validation layer name
const VALIDATION_LAYER: &CStr = unsafe { 
    CStr::from_bytes_with_nul_unchecked(b"VK_LAYER_KHRONOS_validation\0") 
};

impl VulkanContext {
    /// Create a new Vulkan context with Dynamic Rendering enabled
    ///
    /// # Safety
    /// This function creates Vulkan objects and requires proper cleanup via Drop
    pub unsafe fn new(window: &winit::window::Window) -> Result<Self> {
        info!("╔══════════════════════════════════════════════════════════════╗");
        info!("║   VULKAN 1.3 INITIALIZATION - DYNAMIC RENDERING MODE        ║");
        info!("╚══════════════════════════════════════════════════════════════╝");

        // Load Vulkan library
        let entry = Entry::load().context("Failed to load Vulkan library")?;
        
        // Verify Vulkan 1.3 support
        let api_version = match entry.try_enumerate_instance_version()? {
            Some(version) => version,
            None => vk::API_VERSION_1_0,
        };
        
        let major = vk::api_version_major(api_version);
        let minor = vk::api_version_minor(api_version);
        let patch = vk::api_version_patch(api_version);
        info!("📦 Vulkan Instance Version: {}.{}.{}", major, minor, patch);
        
        if api_version < vk::API_VERSION_1_3 {
            return Err(anyhow!(
                "Vulkan 1.3 required for Dynamic Rendering. Found: {}.{}.{}",
                major, minor, patch
            ));
        }

        // Create instance
        let instance = Self::create_instance(&entry, window)?;
        
        // Set up debug messenger (debug builds only)
        let debug_utils = Self::setup_debug_messenger(&entry, &instance)?;
        
        // Create surface
        let surface_loader = khr::surface::Instance::new(&entry, &instance);
        let surface = ash_window::create_surface(
            &entry,
            &instance,
            window.display_handle()?.as_raw(),
            window.window_handle()?.as_raw(),
            None,
        ).context("Failed to create window surface")?;
        info!("✅ Surface created");

        // Select physical device (The 4090 Hunt)
        let (physical_device, physical_device_properties, queue_family_index) = 
            Self::select_physical_device(&instance, &surface_loader, surface)?;
        
        // Create logical device with Dynamic Rendering
        let device = Self::create_logical_device(
            &instance, 
            physical_device, 
            queue_family_index
        )?;
        
        // Get queues
        let graphics_queue = device.get_device_queue(queue_family_index, 0);
        let present_queue = device.get_device_queue(queue_family_index, 0);
        
        info!("═══════════════════════════════════════════════════════════════");
        info!("🔥 VULKAN CONTEXT INITIALIZED: 4090 READY 🔥");
        info!("   Device: {}", 
            CStr::from_ptr(physical_device_properties.device_name.as_ptr())
                .to_string_lossy()
        );
        info!("   API: Vulkan 1.3 | Mode: Dynamic Rendering");
        info!("═══════════════════════════════════════════════════════════════");

        Ok(Self {
            entry,
            instance,
            debug_utils,
            surface_loader,
            surface,
            physical_device,
            physical_device_properties,
            device,
            queue_family_index,
            graphics_queue,
            present_queue,
        })
    }

    /// Create Vulkan instance with required extensions
    unsafe fn create_instance(entry: &Entry, window: &winit::window::Window) -> Result<Instance> {
        let app_name = CString::new("The Chthonic Archive").unwrap();
        let engine_name = CString::new("ASC-NATIVE-CHAIN-RPG").unwrap();
        
        // ash 0.38: Use Default + setters instead of builder()
        let app_info = vk::ApplicationInfo::default()
            .application_name(&app_name)
            .application_version(vk::make_api_version(0, 0, 1, 0))
            .engine_name(&engine_name)
            .engine_version(vk::make_api_version(0, 0, 1, 0))
            .api_version(vk::API_VERSION_1_3);

        // Get required surface extensions
        let mut extensions = ash_window::enumerate_required_extensions(
            window.display_handle()?.as_raw()
        )?.to_vec();
        
        // Add debug utils extension
        #[cfg(debug_assertions)]
        extensions.push(ext::debug_utils::NAME.as_ptr());
        
        info!("📦 Instance extensions: {}", extensions.len());
        for ext in &extensions {
            debug!("   - {}", CStr::from_ptr(*ext).to_string_lossy());
        }

        // Validation layers (debug only)
        let layer_names: Vec<*const c_char>;
        #[cfg(debug_assertions)]
        {
            // Check if validation layer is available
            let available_layers = entry.enumerate_instance_layer_properties()?;
            let validation_available = available_layers.iter().any(|layer| {
                let name = CStr::from_ptr(layer.layer_name.as_ptr());
                name == VALIDATION_LAYER
            });
            
            if validation_available {
                layer_names = vec![VALIDATION_LAYER.as_ptr()];
                info!("✅ Validation layers enabled");
            } else {
                layer_names = vec![];
                warn!("⚠️ Validation layer not available");
            }
        }
        #[cfg(not(debug_assertions))]
        {
            layer_names = vec![];
        }

        // ash 0.38: Use Default + setters
        let create_info = vk::InstanceCreateInfo::default()
            .application_info(&app_info)
            .enabled_extension_names(&extensions)
            .enabled_layer_names(&layer_names);

        let instance = entry
            .create_instance(&create_info, None)
            .context("Failed to create Vulkan instance")?;
        
        info!("✅ Vulkan instance created");
        Ok(instance)
    }

    /// Set up debug messenger for validation layer output
    #[cfg(debug_assertions)]
    unsafe fn setup_debug_messenger(
        entry: &Entry,
        instance: &Instance,
    ) -> Result<Option<DebugContext>> {
        let debug_utils_loader = ext::debug_utils::Instance::new(entry, instance);
        
        // ash 0.38: Use Default + setters
        let messenger_info = vk::DebugUtilsMessengerCreateInfoEXT::default()
            .message_severity(
                vk::DebugUtilsMessageSeverityFlagsEXT::ERROR
                    | vk::DebugUtilsMessageSeverityFlagsEXT::WARNING
                    | vk::DebugUtilsMessageSeverityFlagsEXT::INFO,
            )
            .message_type(
                vk::DebugUtilsMessageTypeFlagsEXT::GENERAL
                    | vk::DebugUtilsMessageTypeFlagsEXT::VALIDATION
                    | vk::DebugUtilsMessageTypeFlagsEXT::PERFORMANCE,
            )
            .pfn_user_callback(Some(debug_callback));

        let messenger = debug_utils_loader
            .create_debug_utils_messenger(&messenger_info, None)
            .context("Failed to create debug messenger")?;
        
        info!("✅ Debug messenger initialized");
        Ok(Some(DebugContext {
            loader: debug_utils_loader,
            messenger,
        }))
    }

    #[cfg(not(debug_assertions))]
    unsafe fn setup_debug_messenger(
        _entry: &Entry,
        _instance: &Instance,
    ) -> Result<Option<DebugContext>> {
        Ok(None)
    }

    /// Select the best physical device (prioritize discrete GPU with most VRAM)
    unsafe fn select_physical_device(
        instance: &Instance,
        surface_loader: &khr::surface::Instance,
        surface: vk::SurfaceKHR,
    ) -> Result<(vk::PhysicalDevice, vk::PhysicalDeviceProperties, u32)> {
        let physical_devices = instance
            .enumerate_physical_devices()
            .context("Failed to enumerate physical devices")?;

        if physical_devices.is_empty() {
            return Err(anyhow!("No Vulkan-capable GPU found"));
        }

        info!("🔍 Scanning {} GPU(s) for RTX 4090...", physical_devices.len());

        // Score each device
        let mut best_device: Option<(vk::PhysicalDevice, vk::PhysicalDeviceProperties, u32, u64)> = None;

        for pdevice in physical_devices {
            let properties = instance.get_physical_device_properties(pdevice);
            let device_name = CStr::from_ptr(properties.device_name.as_ptr()).to_string_lossy();
            
            // Check queue family support
            let queue_families = instance.get_physical_device_queue_family_properties(pdevice);
            let queue_family_index = queue_families
                .iter()
                .enumerate()
                .find_map(|(index, info)| {
                    let supports_graphics = info.queue_flags.contains(vk::QueueFlags::GRAPHICS);
                    let supports_present = surface_loader
                        .get_physical_device_surface_support(pdevice, index as u32, surface)
                        .unwrap_or(false);
                    
                    if supports_graphics && supports_present {
                        Some(index as u32)
                    } else {
                        None
                    }
                });

            let queue_family_index = match queue_family_index {
                Some(idx) => idx,
                None => {
                    debug!("   ❌ {} - No suitable queue family", device_name);
                    continue;
                }
            };

            // Check Dynamic Rendering support
            let mut dynamic_rendering_features = vk::PhysicalDeviceDynamicRenderingFeatures::default();
            let mut features2 = vk::PhysicalDeviceFeatures2::default()
                .push_next(&mut dynamic_rendering_features);
            instance.get_physical_device_features2(pdevice, &mut features2);
            
            if dynamic_rendering_features.dynamic_rendering == vk::FALSE {
                debug!("   ❌ {} - No Dynamic Rendering support", device_name);
                continue;
            }

            // Calculate score
            let mut score: u64 = 0;
            
            // Prioritize discrete GPU
            if properties.device_type == vk::PhysicalDeviceType::DISCRETE_GPU {
                score += 10000;
            }
            
            // Add VRAM to score (from memory properties)
            let memory_properties = instance.get_physical_device_memory_properties(pdevice);
            let vram: u64 = memory_properties.memory_heaps
                [..memory_properties.memory_heap_count as usize]
                .iter()
                .filter(|heap| heap.flags.contains(vk::MemoryHeapFlags::DEVICE_LOCAL))
                .map(|heap| heap.size)
                .sum();
            
            score += vram / (1024 * 1024); // MB as score component
            
            let device_type_str = match properties.device_type {
                vk::PhysicalDeviceType::DISCRETE_GPU => "Discrete",
                vk::PhysicalDeviceType::INTEGRATED_GPU => "Integrated",
                vk::PhysicalDeviceType::VIRTUAL_GPU => "Virtual",
                vk::PhysicalDeviceType::CPU => "CPU",
                _ => "Other",
            };
            
            info!(
                "   📊 {} ({}) - VRAM: {} MB, Score: {}",
                device_name,
                device_type_str,
                vram / (1024 * 1024),
                score
            );

            // Track best device
            if best_device.is_none() || score > best_device.as_ref().unwrap().3 {
                best_device = Some((pdevice, properties, queue_family_index, score));
            }
        }

        let (pdevice, properties, queue_family_index, _score) = best_device
            .ok_or_else(|| anyhow!("No suitable GPU found with Dynamic Rendering support"))?;
        
        let device_name = CStr::from_ptr(properties.device_name.as_ptr()).to_string_lossy();
        info!("✅ Selected GPU: {}", device_name);
        
        Ok((pdevice, properties, queue_family_index))
    }

    /// Create logical device with Dynamic Rendering enabled
    unsafe fn create_logical_device(
        instance: &Instance,
        physical_device: vk::PhysicalDevice,
        queue_family_index: u32,
    ) -> Result<Device> {
        let queue_priorities = [1.0f32];
        let queue_create_info = vk::DeviceQueueCreateInfo::default()
            .queue_family_index(queue_family_index)
            .queue_priorities(&queue_priorities);

        // Device extensions
        let device_extensions = [
            khr::swapchain::NAME.as_ptr(),
            // Dynamic Rendering is core in 1.3, but we can explicitly enable it
            // Ray Tracing extensions will be added in Phase 13:
            // khr::ray_tracing_pipeline::NAME.as_ptr(),
            // khr::acceleration_structure::NAME.as_ptr(),
            // khr::deferred_host_operations::NAME.as_ptr(),
        ];

        // Enable Vulkan 1.3 features (includes Dynamic Rendering - no need for separate feature struct)
        // Note: VkPhysicalDeviceVulkan13Features already contains dynamic_rendering and synchronization2
        // Adding VkPhysicalDeviceDynamicRenderingFeatures separately causes validation error
        let mut vulkan_13_features = vk::PhysicalDeviceVulkan13Features::default()
            .dynamic_rendering(true)
            .synchronization2(true);

        // Base features
        let features = vk::PhysicalDeviceFeatures::default()
            .sampler_anisotropy(true);

        let mut features2 = vk::PhysicalDeviceFeatures2::default()
            .features(features)
            .push_next(&mut vulkan_13_features);

        let queue_create_infos = [queue_create_info];
        let device_create_info = vk::DeviceCreateInfo::default()
            .queue_create_infos(&queue_create_infos)
            .enabled_extension_names(&device_extensions)
            .push_next(&mut features2);

        let device = instance
            .create_device(physical_device, &device_create_info, None)
            .context("Failed to create logical device")?;

        info!("✅ Logical device created with Dynamic Rendering enabled");
        Ok(device)
    }
}

impl Drop for VulkanContext {
    fn drop(&mut self) {
        unsafe {
            info!("🧹 Cleaning up Vulkan context...");
            
            self.device.device_wait_idle().ok();
            self.device.destroy_device(None);
            
            self.surface_loader.destroy_surface(self.surface, None);
            
            if let Some(ref debug) = self.debug_utils {
                debug.loader.destroy_debug_utils_messenger(debug.messenger, None);
            }
            
            self.instance.destroy_instance(None);
            info!("✅ Vulkan context destroyed");
        }
    }
}

/// Debug callback for validation layer messages
#[cfg(debug_assertions)]
unsafe extern "system" fn debug_callback(
    message_severity: vk::DebugUtilsMessageSeverityFlagsEXT,
    message_type: vk::DebugUtilsMessageTypeFlagsEXT,
    p_callback_data: *const vk::DebugUtilsMessengerCallbackDataEXT,
    _user_data: *mut std::ffi::c_void,
) -> vk::Bool32 {
    let callback_data = *p_callback_data;
    let message = if callback_data.p_message.is_null() {
        std::borrow::Cow::Borrowed("(no message)")
    } else {
        CStr::from_ptr(callback_data.p_message).to_string_lossy()
    };

    let type_str = match message_type {
        vk::DebugUtilsMessageTypeFlagsEXT::GENERAL => "GENERAL",
        vk::DebugUtilsMessageTypeFlagsEXT::VALIDATION => "VALIDATION",
        vk::DebugUtilsMessageTypeFlagsEXT::PERFORMANCE => "PERFORMANCE",
        _ => "UNKNOWN",
    };

    match message_severity {
        vk::DebugUtilsMessageSeverityFlagsEXT::ERROR => {
            log::error!("[VK:{}] {}", type_str, message);
        }
        vk::DebugUtilsMessageSeverityFlagsEXT::WARNING => {
            warn!("[VK:{}] {}", type_str, message);
        }
        vk::DebugUtilsMessageSeverityFlagsEXT::INFO => {
            info!("[VK:{}] {}", type_str, message);
        }
        _ => {
            debug!("[VK:{}] {}", type_str, message);
        }
    }

    vk::FALSE
}
