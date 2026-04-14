// tools/ankh-forge/build.rs
//
// Compiles GLSL compute shaders to SPIR-V when the `gpu` feature is active.
// Outputs are placed in OUT_DIR and embedded via `include_bytes!` in gpu-feature code.

fn main() {
    // Only compile shaders when the gpu feature is requested.
    if std::env::var("CARGO_FEATURE_GPU").is_err() {
        return;
    }

    let manifest_dir = std::env::var("CARGO_MANIFEST_DIR").unwrap();
    let workspace_root = std::path::Path::new(&manifest_dir)
        .parent()   // tools/
        .unwrap()
        .parent()   // chthonic-archive/
        .unwrap()
        .to_path_buf();

    let shader_src = workspace_root
        .join("assets")
        .join("shaders")
        .join("trail_decompress.comp.glsl");

    println!(
        "cargo:rerun-if-changed={}",
        shader_src.display()
    );

    if !shader_src.exists() {
        panic!(
            "shader not found: {}\n\
             Expected the LZ4 decompressor at assets/shaders/trail_decompress.comp.glsl",
            shader_src.display()
        );
    }

    let out_dir = std::env::var("OUT_DIR").unwrap();
    let spirv_out = std::path::Path::new(&out_dir).join("trail_decompress.spv");

    // Prefer glslc (Vulkan SDK) for SPIR-V 1.6 output.
    let glslc_result = std::process::Command::new("glslc")
        .arg("--target-env=vulkan1.3")
        .arg("-fshader-stage=compute")
        .arg(&shader_src)
        .arg("-o")
        .arg(&spirv_out)
        .status();

    match glslc_result {
        Ok(status) if status.success() => {
            println!(
                "cargo:warning=trail_decompress.comp.glsl → trail_decompress.spv ({})",
                spirv_out.display()
            );
        }
        _ => {
            panic!(
                "glslc failed to compile {}\n\
                 Install the Vulkan SDK and ensure glslc is in PATH to build --features gpu.\n\
                 Vulkan SDK: https://vulkan.lunarg.com/sdk/home",
                shader_src.display()
            );
        }
    }
}
