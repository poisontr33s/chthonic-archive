//! Vulkan 1.3 Swapchain Management
//!
//! "Your filth is structurally unsound. It leaks. It wobbles."
//! "I shall refine it into a diamond of pure, cutting perversion."
//! — Madam Umeko Ketsuraku
//!
//! This swapchain implementation:
//! - Targets optimal format (BGRA8_SRGB preferred)
//! - Uses FIFO present mode (V-Sync for stability)
//! - Handles window resize gracefully
//! - Prepares images for Dynamic Rendering

use anyhow::{anyhow, Context, Result};
use ash::{khr, vk, Device, Instance};
use log::{debug, info, warn};

/// Swapchain configuration and state
/// 
/// HYBRID SYNC STRATEGY (Per Vulkan Swapchain Semaphore Reuse Guide):
/// - image_available_semaphores: Index by FRAME (we control acquisition timing)
/// - render_finished_semaphores: Index by IMAGE (swapchain controls which image)
/// - in_flight_fences: Index by FRAME (we control frame submission)
pub struct VulkanSwapchain {
    pub loader: khr::swapchain::Device,
    pub swapchain: vk::SwapchainKHR,
    pub images: Vec<vk::Image>,
    pub image_views: Vec<vk::ImageView>,
    pub format: vk::Format,
    pub extent: vk::Extent2D,
    
    // === SYNCHRONIZATION (HYBRID STRATEGY) ===
    // image_available: Frame-indexed (for vkAcquireNextImage)
    pub image_available_semaphores: Vec<vk::Semaphore>,  // Index by current_frame
    // render_finished: IMAGE-indexed (for vkQueuePresentKHR) 
    // This is the KEY FIX - present waits on this, so it must match the image
    pub render_finished_semaphores: Vec<vk::Semaphore>,  // Index by image_index
    // Fences: Frame-indexed (for CPU-GPU sync)
    pub in_flight_fences: Vec<vk::Fence>,                // Index by current_frame
    
    // Track which fence is associated with each swapchain image
    // This prevents using an image that's still being rendered
    pub images_in_flight: Vec<vk::Fence>,  // Index by image_index
    
    // Frame counter (we control this) and currently acquired image
    pub current_frame: usize,
    pub current_image_index: u32,  // The image we acquired for this frame
    pub frames_in_flight: usize,
}

/// Swapchain support details queried from physical device
pub struct SwapchainSupportDetails {
    pub capabilities: vk::SurfaceCapabilitiesKHR,
    pub formats: Vec<vk::SurfaceFormatKHR>,
    pub present_modes: Vec<vk::PresentModeKHR>,
}

impl VulkanSwapchain {
    /// Maximum frames that can be processed simultaneously
    pub const MAX_FRAMES_IN_FLIGHT: usize = 2;

    /// Create a new swapchain
    ///
    /// # Safety
    /// Requires valid Vulkan handles
    pub unsafe fn new(
        instance: &Instance,
        device: &Device,
        physical_device: vk::PhysicalDevice,
        surface_loader: &khr::surface::Instance,
        surface: vk::SurfaceKHR,
        queue_family_index: u32,
        window_size: (u32, u32),
    ) -> Result<Self> {
        info!("╔══════════════════════════════════════════════════════════════╗");
        info!("║   SWAPCHAIN CREATION - The Steel Lotus Unfolds              ║");
        info!("╚══════════════════════════════════════════════════════════════╝");

        // Query swapchain support
        let support = Self::query_swapchain_support(
            physical_device,
            surface_loader,
            surface,
        )?;

        // Select optimal configuration
        let format = Self::select_format(&support.formats);
        let present_mode = Self::select_present_mode(&support.present_modes);
        let extent = Self::select_extent(&support.capabilities, window_size);

        info!("   Format: {:?}", format.format);
        info!("   Color Space: {:?}", format.color_space);
        info!("   Present Mode: {:?}", present_mode);
        info!("   Extent: {}x{}", extent.width, extent.height);

        // Calculate image count (prefer triple buffering)
        let image_count = {
            let min = support.capabilities.min_image_count;
            let max = if support.capabilities.max_image_count == 0 {
                u32::MAX
            } else {
                support.capabilities.max_image_count
            };
            (min + 1).min(max)
        };
        info!("   Image Count: {}", image_count);

        // Create swapchain
        let queue_family_indices = [queue_family_index];
        let swapchain_create_info = vk::SwapchainCreateInfoKHR::default()
            .surface(surface)
            .min_image_count(image_count)
            .image_format(format.format)
            .image_color_space(format.color_space)
            .image_extent(extent)
            .image_array_layers(1)
            .image_usage(vk::ImageUsageFlags::COLOR_ATTACHMENT)
            .image_sharing_mode(vk::SharingMode::EXCLUSIVE)
            .queue_family_indices(&queue_family_indices)
            .pre_transform(support.capabilities.current_transform)
            .composite_alpha(vk::CompositeAlphaFlagsKHR::OPAQUE)
            .present_mode(present_mode)
            .clipped(true)
            .old_swapchain(vk::SwapchainKHR::null());

        let loader = khr::swapchain::Device::new(instance, device);
        let swapchain = loader
            .create_swapchain(&swapchain_create_info, None)
            .context("Failed to create swapchain")?;

        info!("✅ Swapchain created");

        // Get swapchain images
        let images = loader.get_swapchain_images(swapchain)?;
        let image_count = images.len();
        info!("   Retrieved {} swapchain images", image_count);

        // Create image views for each swapchain image
        let image_views = Self::create_image_views(device, &images, format.format)?;

        // Create synchronization primitives with HYBRID indexing
        // Per Vulkan Guide: render_finished must be IMAGE-indexed for present safety
        let frames_in_flight = Self::MAX_FRAMES_IN_FLIGHT;
        let (image_available_semaphores, render_finished_semaphores, in_flight_fences) =
            Self::create_sync_objects_hybrid(device, frames_in_flight, image_count)?;

        // Track which images are in flight (initially none)
        let images_in_flight = vec![vk::Fence::null(); image_count];

        info!("═══════════════════════════════════════════════════════════════");
        info!("🔥 SWAPCHAIN READY: {} frames in flight, {} images", frames_in_flight, image_count);
        info!("═══════════════════════════════════════════════════════════════");

        Ok(Self {
            loader,
            swapchain,
            images,
            image_views,
            format: format.format,
            extent,
            image_available_semaphores,
            render_finished_semaphores,
            in_flight_fences,
            images_in_flight,
            current_frame: 0,
            current_image_index: 0,  // Will be set on first acquire
            frames_in_flight,
        })
    }

    /// Query swapchain support details
    unsafe fn query_swapchain_support(
        physical_device: vk::PhysicalDevice,
        surface_loader: &khr::surface::Instance,
        surface: vk::SurfaceKHR,
    ) -> Result<SwapchainSupportDetails> {
        let capabilities = surface_loader
            .get_physical_device_surface_capabilities(physical_device, surface)
            .context("Failed to get surface capabilities")?;

        let formats = surface_loader
            .get_physical_device_surface_formats(physical_device, surface)
            .context("Failed to get surface formats")?;

        let present_modes = surface_loader
            .get_physical_device_surface_present_modes(physical_device, surface)
            .context("Failed to get present modes")?;

        if formats.is_empty() || present_modes.is_empty() {
            return Err(anyhow!("Inadequate swapchain support"));
        }

        Ok(SwapchainSupportDetails {
            capabilities,
            formats,
            present_modes,
        })
    }

    /// Select optimal surface format (prefer BGRA8 SRGB)
    fn select_format(formats: &[vk::SurfaceFormatKHR]) -> vk::SurfaceFormatKHR {
        // Prefer BGRA8 with SRGB color space (The 69.96 Signature)
        formats
            .iter()
            .find(|f| {
                f.format == vk::Format::B8G8R8A8_SRGB
                    && f.color_space == vk::ColorSpaceKHR::SRGB_NONLINEAR
            })
            .cloned()
            .or_else(|| {
                // Fallback: any SRGB format
                formats.iter().find(|f| {
                    f.color_space == vk::ColorSpaceKHR::SRGB_NONLINEAR
                }).cloned()
            })
            .unwrap_or(formats[0])
    }

    /// Select present mode - use FIFO for maximum stability during development
    fn select_present_mode(modes: &[vk::PresentModeKHR]) -> vk::PresentModeKHR {
        // During development, prefer FIFO (V-Sync) for stability
        // FIFO is always guaranteed and prevents tearing/sync issues
        // We can switch to MAILBOX later for low-latency gameplay
        if modes.contains(&vk::PresentModeKHR::FIFO) {
            info!("   Using FIFO present mode (V-Sync, stable)");
            return vk::PresentModeKHR::FIFO;
        }
        
        // Fallback (should never happen - FIFO is mandatory)
        info!("   Using IMMEDIATE present mode (fallback)");
        vk::PresentModeKHR::IMMEDIATE
    }

    /// Select swapchain extent matching window size
    fn select_extent(
        capabilities: &vk::SurfaceCapabilitiesKHR,
        window_size: (u32, u32),
    ) -> vk::Extent2D {
        // If currentExtent is 0xFFFFFFFF, we can pick our own
        if capabilities.current_extent.width != u32::MAX {
            return capabilities.current_extent;
        }

        vk::Extent2D {
            width: window_size.0.clamp(
                capabilities.min_image_extent.width,
                capabilities.max_image_extent.width,
            ),
            height: window_size.1.clamp(
                capabilities.min_image_extent.height,
                capabilities.max_image_extent.height,
            ),
        }
    }

    /// Create image views for swapchain images
    unsafe fn create_image_views(
        device: &Device,
        images: &[vk::Image],
        format: vk::Format,
    ) -> Result<Vec<vk::ImageView>> {
        images
            .iter()
            .enumerate()
            .map(|(i, &image)| {
                let create_info = vk::ImageViewCreateInfo::default()
                    .image(image)
                    .view_type(vk::ImageViewType::TYPE_2D)
                    .format(format)
                    .components(vk::ComponentMapping {
                        r: vk::ComponentSwizzle::IDENTITY,
                        g: vk::ComponentSwizzle::IDENTITY,
                        b: vk::ComponentSwizzle::IDENTITY,
                        a: vk::ComponentSwizzle::IDENTITY,
                    })
                    .subresource_range(vk::ImageSubresourceRange {
                        aspect_mask: vk::ImageAspectFlags::COLOR,
                        base_mip_level: 0,
                        level_count: 1,
                        base_array_layer: 0,
                        layer_count: 1,
                    });

                device
                    .create_image_view(&create_info, None)
                    .with_context(|| format!("Failed to create image view {}", i))
            })
            .collect()
    }

    /// Create synchronization primitives with HYBRID indexing strategy
    /// 
    /// Per Vulkan Swapchain Semaphore Reuse Guide:
    /// - image_available: FRAME-indexed (we control acquire timing)
    /// - render_finished: IMAGE-indexed (must match swapchain image)
    /// - in_flight_fences: FRAME-indexed (CPU-GPU sync)
    unsafe fn create_sync_objects_hybrid(
        device: &Device,
        frames_in_flight: usize,
        image_count: usize,
    ) -> Result<(Vec<vk::Semaphore>, Vec<vk::Semaphore>, Vec<vk::Fence>)> {
        let semaphore_info = vk::SemaphoreCreateInfo::default();
        let fence_info = vk::FenceCreateInfo::default()
            .flags(vk::FenceCreateFlags::SIGNALED); // Start signaled so first wait doesn't hang

        // image_available: one per frame in flight (FRAME-indexed)
        let mut image_available = Vec::with_capacity(frames_in_flight);
        for i in 0..frames_in_flight {
            image_available.push(
                device.create_semaphore(&semaphore_info, None)
                    .with_context(|| format!("Failed to create image_available semaphore {}", i))?
            );
        }
        
        // render_finished: one per swapchain IMAGE (IMAGE-indexed) - THE KEY FIX
        // This semaphore is used in vkQueuePresentKHR which waits for rendering
        // It can only be reused when its associated image is re-acquired
        let mut render_finished = Vec::with_capacity(image_count);
        for i in 0..image_count {
            render_finished.push(
                device.create_semaphore(&semaphore_info, None)
                    .with_context(|| format!("Failed to create render_finished semaphore for image {}", i))?
            );
        }
        
        // in_flight_fences: one per frame in flight (FRAME-indexed)
        let mut in_flight = Vec::with_capacity(frames_in_flight);
        for i in 0..frames_in_flight {
            in_flight.push(
                device.create_fence(&fence_info, None)
                    .with_context(|| format!("Failed to create in_flight fence {}", i))?
            );
        }

        info!("✅ Created {} image_available semaphores (frame-indexed)", frames_in_flight);
        info!("✅ Created {} render_finished semaphores (IMAGE-indexed)", image_count);
        info!("✅ Created {} in_flight fences (frame-indexed)", frames_in_flight);
        Ok((image_available, render_finished, in_flight))
    }

    /// Acquire next swapchain image for rendering
    ///
    /// Returns (image_index, needs_resize)
    /// Acquire next swapchain image for rendering
    ///
    /// Returns (image_index, needs_resize)
    /// HYBRID strategy: FRAME-indexed acquire semaphore, stores image_index for present
    pub unsafe fn acquire_next_image(&mut self, device: &Device) -> Result<(u32, bool)> {
        // Wait for this frame slot's fence to be signaled
        // (i.e., wait for the GPU to finish with the frame that was using this slot)
        let fence = self.in_flight_fences[self.current_frame];
        device
            .wait_for_fences(&[fence], true, u64::MAX)
            .context("Failed to wait for frame fence")?;

        // Use FRAME-indexed semaphore for acquire
        let semaphore = self.image_available_semaphores[self.current_frame];
        
        match self.loader.acquire_next_image(
            self.swapchain,
            u64::MAX,
            semaphore,
            vk::Fence::null(),
        ) {
            Ok((image_index, suboptimal)) => {
                // Store the acquired image index for use in present()
                self.current_image_index = image_index;
                
                // Check if this specific IMAGE is still being used by a previous frame
                let image_fence = self.images_in_flight[image_index as usize];
                if image_fence != vk::Fence::null() && image_fence != fence {
                    // A different frame is still using this image - wait for it
                    device
                        .wait_for_fences(&[image_fence], true, u64::MAX)
                        .context("Failed to wait for image fence")?;
                }
                
                // Mark this image as being used by the current frame's fence
                self.images_in_flight[image_index as usize] = fence;
                
                if suboptimal {
                    debug!("Swapchain suboptimal");
                }
                Ok((image_index, false))
            }
            Err(vk::Result::ERROR_OUT_OF_DATE_KHR) => {
                info!("🔄 Swapchain out of date - recreating");
                Ok((0, true))
            }
            Err(e) => Err(anyhow!("Failed to acquire swapchain image: {:?}", e)),
        }
    }

    /// Present rendered image to screen
    ///
    /// Returns true if resize is needed
    /// HYBRID strategy: Uses IMAGE-indexed render_finished semaphore
    pub unsafe fn present(
        &mut self,
        queue: vk::Queue,
        image_index: u32,
    ) -> Result<bool> {
        // KEY FIX: Use IMAGE-indexed semaphore for present wait
        // This ensures the semaphore won't be reused until this image is re-acquired
        let wait_semaphores = [self.render_finished_semaphores[image_index as usize]];
        let swapchains = [self.swapchain];
        let image_indices = [image_index];

        let present_info = vk::PresentInfoKHR::default()
            .wait_semaphores(&wait_semaphores)
            .swapchains(&swapchains)
            .image_indices(&image_indices);

        let result = self.loader.queue_present(queue, &present_info);
        
        // Advance to next frame slot (we control this counter)
        self.current_frame = (self.current_frame + 1) % self.frames_in_flight;

        match result {
            Ok(suboptimal) => {
                if suboptimal {
                    debug!("Present suboptimal");
                }
                Ok(false)
            }
            Err(vk::Result::ERROR_OUT_OF_DATE_KHR) => {
                info!("🔄 Present out of date - recreating swapchain");
                Ok(true)
            }
            Err(e) => Err(anyhow!("Failed to present: {:?}", e)),
        }
    }

    /// Recreate swapchain (for window resize)
    pub unsafe fn recreate(
        &mut self,
        instance: &Instance,
        device: &Device,
        physical_device: vk::PhysicalDevice,
        surface_loader: &khr::surface::Instance,
        surface: vk::SurfaceKHR,
        queue_family_index: u32,
        window_size: (u32, u32),
    ) -> Result<()> {
        info!("🔄 Recreating swapchain for new size: {}x{}", window_size.0, window_size.1);

        // Wait for device to be idle
        device.device_wait_idle()?;

        // Clean up old resources
        self.cleanup_views(device);

        // Query new support
        let support = Self::query_swapchain_support(
            physical_device,
            surface_loader,
            surface,
        )?;

        let format = Self::select_format(&support.formats);
        let present_mode = Self::select_present_mode(&support.present_modes);
        let extent = Self::select_extent(&support.capabilities, window_size);

        let image_count = {
            let min = support.capabilities.min_image_count;
            let max = if support.capabilities.max_image_count == 0 {
                u32::MAX
            } else {
                support.capabilities.max_image_count
            };
            (min + 1).min(max)
        };

        // Create new swapchain referencing old one
        let queue_family_indices = [queue_family_index];
        let swapchain_create_info = vk::SwapchainCreateInfoKHR::default()
            .surface(surface)
            .min_image_count(image_count)
            .image_format(format.format)
            .image_color_space(format.color_space)
            .image_extent(extent)
            .image_array_layers(1)
            .image_usage(vk::ImageUsageFlags::COLOR_ATTACHMENT)
            .image_sharing_mode(vk::SharingMode::EXCLUSIVE)
            .queue_family_indices(&queue_family_indices)
            .pre_transform(support.capabilities.current_transform)
            .composite_alpha(vk::CompositeAlphaFlagsKHR::OPAQUE)
            .present_mode(present_mode)
            .clipped(true)
            .old_swapchain(self.swapchain);

        let old_swapchain = self.swapchain;
        self.swapchain = self.loader
            .create_swapchain(&swapchain_create_info, None)
            .context("Failed to recreate swapchain")?;

        // Destroy old swapchain
        self.loader.destroy_swapchain(old_swapchain, None);

        // Get new images
        self.images = self.loader.get_swapchain_images(self.swapchain)?;
        let new_image_count = self.images.len();
        self.image_views = Self::create_image_views(device, &self.images, format.format)?;
        self.format = format.format;
        self.extent = extent;
        
        // If image count changed, recreate render_finished semaphores (IMAGE-indexed)
        let old_image_count = self.render_finished_semaphores.len();
        if new_image_count != old_image_count {
            // Destroy old render_finished semaphores
            for &semaphore in &self.render_finished_semaphores {
                device.destroy_semaphore(semaphore, None);
            }
            // Create new ones matching new image count
            let semaphore_info = vk::SemaphoreCreateInfo::default();
            self.render_finished_semaphores = Vec::with_capacity(new_image_count);
            for i in 0..new_image_count {
                self.render_finished_semaphores.push(
                    device.create_semaphore(&semaphore_info, None)
                        .with_context(|| format!("Failed to recreate render_finished semaphore {}", i))?
                );
            }
            debug!("🔄 Recreated {} render_finished semaphores for new image count", new_image_count);
        }
        
        // Reset image tracking
        self.images_in_flight = vec![vk::Fence::null(); new_image_count];
        
        // Reset frame and image index
        self.current_frame = 0;
        self.current_image_index = 0;

        info!("✅ Swapchain recreated: {}x{}", extent.width, extent.height);
        Ok(())
    }

    /// Clean up image views (before recreate or destroy)
    unsafe fn cleanup_views(&mut self, device: &Device) {
        for &view in &self.image_views {
            device.destroy_image_view(view, None);
        }
        self.image_views.clear();
    }

    /// Clean up all swapchain resources
    pub unsafe fn cleanup(&mut self, device: &Device) {
        debug!("🧹 Cleaning up swapchain...");

        // Wait for device idle
        device.device_wait_idle().ok();

        // Destroy sync objects
        for &semaphore in &self.image_available_semaphores {
            device.destroy_semaphore(semaphore, None);
        }
        for &semaphore in &self.render_finished_semaphores {
            device.destroy_semaphore(semaphore, None);
        }
        for &fence in &self.in_flight_fences {
            device.destroy_fence(fence, None);
        }

        // Destroy image views
        self.cleanup_views(device);

        // Destroy swapchain
        self.loader.destroy_swapchain(self.swapchain, None);

        debug!("✅ Swapchain cleaned up");
    }

    /// Get current sync objects for rendering (HYBRID indexing)
    /// 
    /// Returns (image_available_semaphore, render_finished_semaphore, fence)
    /// - image_available: FRAME-indexed (for acquire)
    /// - render_finished: IMAGE-indexed (for present - must be called after acquire!)
    /// - fence: FRAME-indexed (for CPU-GPU sync)
    pub fn current_sync(&self) -> (vk::Semaphore, vk::Semaphore, vk::Fence) {
        (
            self.image_available_semaphores[self.current_frame],
            // KEY: Use IMAGE-indexed render_finished semaphore
            self.render_finished_semaphores[self.current_image_index as usize],
            self.in_flight_fences[self.current_frame],
        )
    }
}
