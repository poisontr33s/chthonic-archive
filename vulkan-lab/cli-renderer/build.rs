// @SID: CLI_RENDERER_BUILD_RS_V0
// Compiles GLSL compute shaders → SPIR-V at cargo build time.
// glslc path: C:\VulkanSDK\1.4.341.1\Bin\glslc.exe (frozen in vulkan-lab/CLAUDE.md)
// Output: shaders/*.spv (alongside .glsl sources, included via include_bytes! in main.rs)

use std::{path::PathBuf, process::Command};

fn main() {
    let shader_dir = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap()).join("shaders");
    let glslc = r"C:\VulkanSDK\1.4.341.1\Bin\glslc.exe";

    for shader in ["euler_score.comp.glsl", "ascii_downsample.comp.glsl", "dirty_diff.comp.glsl", "ascii_dungeon.comp.glsl", "iso_render.comp.glsl", "archipelago_field.comp.glsl", "archipelago_diffuse.comp.glsl"] {
        let src = shader_dir.join(shader);
        let spv = shader_dir.join(shader.trim_end_matches(".glsl").to_string() + ".spv");

        // Infer -fshader-stage from the second-to-last extension (e.g. ".comp" → "compute").
        let stage = shader
            .trim_end_matches(".glsl")
            .rsplit_once('.')
            .map(|(_, s)| match s {
                "vert" => "vertex",
                "frag" => "fragment",
                "comp" => "compute",
                "geom" => "geometry",
                "tesc" => "tesscontrol",
                "tese" => "tesseval",
                other  => other,
            })
            .unwrap_or("compute");

        println!("cargo:rerun-if-changed={}", src.display());

        let status = Command::new(glslc)
            .args(["--target-env=vulkan1.3", &format!("-fshader-stage={stage}"), "-o"])
            .arg(&spv)
            .arg(&src)
            .status()
            .unwrap_or_else(|e| panic!(
                "glslc not found at {glslc}\n  {e}\n  Install Vulkan SDK 1.4.341.1 at C:\\VulkanSDK\\"
            ));

        assert!(status.success(), "glslc failed for {shader} — check GLSL syntax");
    }
}
