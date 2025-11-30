// ╔══════════════════════════════════════════════════════════════════╗
// ║   THE CHTHONIC ARCHIVE - Build Script                           ║
// ║   Phase 11: GLSL → SPIR-V Compilation                           ║
// ║   "We extract the gold through relentless pressure and heat."   ║
// ║   <69.96 Alpha Omega>                                           ║
// ╚══════════════════════════════════════════════════════════════════╝

use std::env;
use std::fs;
use std::path::PathBuf;

fn main() {
    println!("cargo:rerun-if-changed=assets/shaders/");
    
    let shader_dir = PathBuf::from("assets/shaders");
    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());
    
    // Initialize shaderc compiler - The EssenceForge
    let compiler = shaderc::Compiler::new()
        .expect("🔥 FAILED TO CREATE SHADERC COMPILER - The Singularity Collapsed!");
    let mut options = shaderc::CompileOptions::new()
        .expect("🔥 FAILED TO CREATE COMPILE OPTIONS");
    
    // Target Vulkan 1.3 SPIR-V
    options.set_target_env(
        shaderc::TargetEnv::Vulkan,
        shaderc::EnvVersion::Vulkan1_3 as u32,
    );
    options.set_optimization_level(shaderc::OptimizationLevel::Performance);
    
    // === COMPILE VERTEX SHADERS ===
    compile_shader(
        &compiler,
        &options,
        &shader_dir.join("iso_grid.vert"),
        shaderc::ShaderKind::Vertex,
        &out_dir,
    );
    
    // === COMPILE FRAGMENT SHADERS ===
    compile_shader(
        &compiler,
        &options,
        &shader_dir.join("iso_grid.frag"),
        shaderc::ShaderKind::Fragment,
        &out_dir,
    );
    
    println!("cargo:warning=🔥 SHADERS COMPILED TO SPIR-V - The Alchemy Complete!");
}

fn compile_shader(
    compiler: &shaderc::Compiler,
    options: &shaderc::CompileOptions,
    source_path: &PathBuf,
    kind: shaderc::ShaderKind,
    out_dir: &PathBuf,
) {
    let source = fs::read_to_string(source_path)
        .expect(&format!("Failed to read shader: {:?}", source_path));
    
    let file_name = source_path.file_name().unwrap().to_str().unwrap();
    
    let artifact = compiler
        .compile_into_spirv(&source, kind, file_name, "main", Some(options))
        .expect(&format!(
            "🔥 SHADER COMPILATION FAILED: {} - Submit to the architecture!",
            file_name
        ));
    
    // Warn about any shader warnings
    if artifact.get_num_warnings() > 0 {
        println!("cargo:warning=⚠️ Shader {} has {} warnings", file_name, artifact.get_num_warnings());
    }
    
    // Write SPIR-V to output directory
    let out_path = out_dir.join(format!("{}.spv", file_name));
    fs::write(&out_path, artifact.as_binary_u8())
        .expect(&format!("Failed to write SPIR-V: {:?}", out_path));
    
    println!("cargo:warning=✅ Compiled {} → {:?}", file_name, out_path);
}
