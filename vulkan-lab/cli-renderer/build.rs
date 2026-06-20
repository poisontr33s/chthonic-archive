// @SID: CLI_RENDERER_BUILD_RS_V0
// Compiles GLSL compute shaders → SPIR-V at cargo build time.
// glslc is resolved from $VULKAN_SDK\Bin (tracks the installed SDK; never a frozen version path —
// a hardcoded 1.4.341.1 here broke on the SDK upgrade to 1.4.350.0 with os error 2).
// Output: shaders/*.spv (alongside .glsl sources, included via include_bytes! in main.rs)

use std::{path::PathBuf, process::Command};

fn main() {
    let shader_dir = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap()).join("shaders");
    let vulkan_sdk = std::env::var("VULKAN_SDK")
        .expect("VULKAN_SDK is not set — install the Vulkan SDK and restart the shell");
    let glslc = format!(r"{vulkan_sdk}\Bin\glslc.exe");

    for shader in ["euler_score.comp.glsl", "ascii_downsample.comp.glsl", "dirty_diff.comp.glsl", "ascii_dungeon.comp.glsl", "iso_render.comp.glsl", "archipelago_field.comp.glsl", "archipelago_diffuse.comp.glsl", "archipelago_advect.comp.glsl"] {
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

        let status = Command::new(&glslc)
            .args(["--target-env=vulkan1.3", &format!("-fshader-stage={stage}"), "-o"])
            .arg(&spv)
            .arg(&src)
            .status()
            .unwrap_or_else(|e| panic!(
                "glslc not found at {glslc}\n  {e}\n  Check the Vulkan SDK at $VULKAN_SDK\\Bin"
            ));

        assert!(status.success(), "glslc failed for {shader} — check GLSL syntax");
    }
}
