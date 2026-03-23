// ╔══════════════════════════════════════════════════════════════════
// ║ THE CHTHONIC ARCHIVE - Build Script
// ║ Phase 11: GLSL → SPIR-V Compilation
// ║ "We extract the gold through relentless pressure and heat."
// ║ <69.96 Alpha Omega>
// ╚══════════════════════════════════════════════════════════════════

//! GLSL → SPIR-V Shader Compilation Build Script
//!
//! @SID:    BUILD_SHADER_COMPILER_V1
//! @Shabti: Build Script

use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

#[derive(Debug)]
enum ShaderCompilerBackend {
    Glslc(PathBuf),
    Shaderc,
}

fn main() {
    println!("cargo:rerun-if-changed=assets/shaders/");
    println!("cargo:rerun-if-changed=assets/shaders/hlsl/");
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-env-changed=CHTHONIC_SHADER_BACKEND");

    let shader_dir = PathBuf::from("assets/shaders");
    let hlsl_dir = shader_dir.join("hlsl");
    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());
    let backend = select_shader_compiler_backend();
    let dxc = detect_dxc();

    // shaderc fallback context: used only when glslc is unavailable or forced off.
    let (shaderc_compiler, shaderc_options) = if matches!(backend, ShaderCompilerBackend::Shaderc)
    {
        let compiler = shaderc::Compiler::new()
            .expect("🔥 FAILED TO CREATE SHADERC COMPILER - The Singularity Collapsed!");
        let mut options = shaderc::CompileOptions::new()
            .expect("🔥 FAILED TO CREATE COMPILE OPTIONS");

        // shaderc 0.8 tops out at Vulkan 1.3 target flags.
        options.set_target_env(
            shaderc::TargetEnv::Vulkan,
            shaderc::EnvVersion::Vulkan1_3 as u32,
        );
        options.set_optimization_level(shaderc::OptimizationLevel::Performance);
        (Some(compiler), Some(options))
    } else {
        (None, None)
    };

    let shader_sources = discover_shader_sources(&shader_dir);
    if shader_sources.is_empty() {
        panic!(
            "No shader sources found in {} (expected extensions: .vert/.frag/.comp/...)",
            shader_dir.display()
        );
    }

    let mut manifest = Vec::with_capacity(shader_sources.len());
    for source_path in shader_sources {
        let stage = shader_kind_for_path(&source_path)
            .unwrap_or_else(|| panic!("Unsupported shader stage: {}", source_path.display()));
        let out_path = compile_shader(
            &backend,
            shaderc_compiler.as_ref(),
            shaderc_options.as_ref(),
            &shader_dir,
            &source_path,
            stage,
            &out_dir,
        );

        let relative = source_path.strip_prefix(&shader_dir).unwrap_or(&source_path);
        let source_key = relative.to_string_lossy().replace('\\', "/");
        let artifact_name = out_path
            .file_name()
            .map_or_else(|| String::from(""), |n| n.to_string_lossy().into_owned());
        manifest.push(format!("{source_key}={artifact_name}"));
    }

    manifest.sort();
    let manifest_path = out_dir.join("shader_manifest.txt");
    fs::write(&manifest_path, manifest.join("\n"))
        .unwrap_or_else(|_| panic!("Failed to write shader manifest: {}", manifest_path.display()));

    let hlsl_sources = discover_hlsl_sources(&hlsl_dir);
    if !hlsl_sources.is_empty() && dxc.is_none() {
        println!(
            "cargo:warning=⚠️ HLSL sources discovered in {} but `dxc` was not found; HLSL runtime selection will be unavailable",
            hlsl_dir.display()
        );
    }

    for source_path in hlsl_sources {
        let profile = hlsl_profile_for_path(&source_path)
            .unwrap_or_else(|| panic!("Unsupported HLSL shader stage: {}", source_path.display()));
        let out_path = compile_hlsl_shader(dxc.as_deref(), &source_path, profile, &out_dir);

        let relative = source_path.strip_prefix(&shader_dir).unwrap_or(&source_path);
        let source_key = relative.to_string_lossy().replace('\\', "/");
        let artifact_name = out_path
            .file_name()
            .map_or_else(|| String::from(""), |n| n.to_string_lossy().into_owned());
        println!("cargo:rerun-if-changed={}", source_path.display());
        fs::write(
            out_dir.join(format!("{artifact_name}.meta")),
            format!("{source_key}\nprofile={profile}\n"),
        )
        .unwrap_or_else(|_| panic!("Failed to write HLSL artifact metadata for {}", source_path.display()));
    }
}

fn select_shader_compiler_backend() -> ShaderCompilerBackend {
    let forced = env::var("CHTHONIC_SHADER_BACKEND").ok();
    match forced.as_deref() {
        Some("shaderc") => ShaderCompilerBackend::Shaderc,
        Some("glslc") => {
            let glslc = detect_glslc()
                .expect("CHTHONIC_SHADER_BACKEND=glslc set, but `glslc` was not found in PATH");
            ShaderCompilerBackend::Glslc(glslc)
        }
        Some(other) => panic!(
            "Unsupported CHTHONIC_SHADER_BACKEND={other}. Use `glslc` or `shaderc`."
        ),
        None => detect_glslc()
            .map(ShaderCompilerBackend::Glslc)
            .unwrap_or(ShaderCompilerBackend::Shaderc),
    }
}

fn detect_glslc() -> Option<PathBuf> {
    let glslc = PathBuf::from("glslc");
    let output = Command::new(&glslc).arg("--version").output().ok()?;
    if output.status.success() {
        Some(glslc)
    } else {
        None
    }
}

fn detect_dxc() -> Option<PathBuf> {
    let dxc = PathBuf::from("dxc");
    let output = Command::new(&dxc).arg("-help").output().ok()?;
    if output.status.success() {
        Some(dxc)
    } else {
        None
    }
}

fn compile_shader(
    backend: &ShaderCompilerBackend,
    compiler: Option<&shaderc::Compiler>,
    options: Option<&shaderc::CompileOptions>,
    shader_root: &Path,
    source_path: &Path,
    kind: shaderc::ShaderKind,
    out_dir: &Path,
) -> PathBuf {
    let out_name = output_shader_artifact_name(shader_root, source_path);
    let out_path = out_dir.join(out_name);

    match backend {
        ShaderCompilerBackend::Glslc(glslc_path) => {
            compile_shader_with_glslc(glslc_path, source_path, kind, &out_path)
        }
        ShaderCompilerBackend::Shaderc => compile_shader_with_shaderc(
            compiler.expect("shaderc compiler unavailable"),
            options.expect("shaderc compile options unavailable"),
            source_path,
            kind,
            &out_path,
        ),
    }

    out_path
}

fn compile_hlsl_shader(
    dxc_path: Option<&Path>,
    source_path: &Path,
    profile: &'static str,
    out_dir: &Path,
) -> PathBuf {
    let out_name = format!(
        "{}.spv",
        source_path
            .file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("shader.hlsl")
    );
    let out_path = out_dir.join(out_name);

    let Some(dxc_path) = dxc_path else {
        return out_path;
    };

    let output = Command::new(dxc_path)
        .arg("-spirv")
        .arg("-fspv-target-env=vulkan1.3")
        .arg("-E")
        .arg("main")
        .arg("-T")
        .arg(profile)
        .arg("-Fo")
        .arg(&out_path)
        .arg(source_path)
        .output()
        .unwrap_or_else(|_| panic!("Failed to execute dxc for {}", source_path.display()));

    let stderr = String::from_utf8_lossy(&output.stderr);
    if !output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        panic!(
            "🔥 DXC COMPILATION FAILED: {}\nstdout:\n{}\nstderr:\n{}",
            source_path.display(),
            stdout,
            stderr
        );
    }

    for line in stderr.lines() {
        if line.to_ascii_lowercase().contains("warning") {
            println!("cargo:warning={line}");
        }
    }

    out_path
}

fn compile_shader_with_shaderc(
    compiler: &shaderc::Compiler,
    options: &shaderc::CompileOptions,
    source_path: &Path,
    kind: shaderc::ShaderKind,
    out_path: &Path,
) {
    let source = fs::read_to_string(source_path)
        .unwrap_or_else(|_| panic!("Failed to read shader: {0}", source_path.display()));

    let file_name = source_path.file_name().unwrap().to_str().unwrap();

    let artifact = compiler
        .compile_into_spirv(&source, kind, file_name, "main", Some(options))
        .unwrap_or_else(|_| {
            panic!(
                "🔥 SHADER COMPILATION FAILED: {file_name} - Submit to the architecture!"
            )
        });

    // Warn about actual shader warnings.
    if artifact.get_num_warnings() > 0 {
        println!(
            "cargo:warning=⚠️ Shader {file_name} has {} warnings",
            artifact.get_num_warnings()
        );
    }

    fs::write(out_path, artifact.as_binary_u8())
        .unwrap_or_else(|_| panic!("Failed to write SPIR-V: {}", out_path.display()));
}

fn compile_shader_with_glslc(
    glslc_path: &Path,
    source_path: &Path,
    kind: shaderc::ShaderKind,
    out_path: &Path,
) {
    let stage = glslc_stage(kind);
    let output = Command::new(glslc_path)
        .arg(source_path)
        .arg(format!("-fshader-stage={stage}"))
        .arg("--target-env=vulkan1.4")
        .arg("--target-spv=spv1.6")
        .arg("-O")
        .arg("-o")
        .arg(out_path)
        .output()
        .unwrap_or_else(|_| panic!("Failed to execute glslc for {}", source_path.display()));

    let stderr = String::from_utf8_lossy(&output.stderr);
    if !output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        panic!(
            "🔥 GLSLC COMPILATION FAILED: {}\nstdout:\n{}\nstderr:\n{}",
            source_path.display(),
            stdout,
            stderr
        );
    }

    // Preserve diagnostics: only forward warning lines as Cargo warnings.
    for line in stderr.lines() {
        if line.to_ascii_lowercase().contains("warning") {
            println!("cargo:warning={line}");
        }
    }
}

fn glslc_stage(kind: shaderc::ShaderKind) -> &'static str {
    match kind {
        shaderc::ShaderKind::Vertex => "vert",
        shaderc::ShaderKind::Fragment => "frag",
        shaderc::ShaderKind::Compute => "comp",
        shaderc::ShaderKind::Geometry => "geom",
        shaderc::ShaderKind::TessControl => "tesc",
        shaderc::ShaderKind::TessEvaluation => "tese",
        shaderc::ShaderKind::RayGeneration => "rgen",
        shaderc::ShaderKind::AnyHit => "rahit",
        shaderc::ShaderKind::ClosestHit => "rchit",
        shaderc::ShaderKind::Miss => "rmiss",
        shaderc::ShaderKind::Intersection => "rint",
        shaderc::ShaderKind::Callable => "rcall",
        shaderc::ShaderKind::Task => "task",
        shaderc::ShaderKind::Mesh => "mesh",
        _ => panic!("Unsupported shader kind for glslc stage mapping: {kind:?}"),
    }
}

fn discover_shader_sources(shader_dir: &Path) -> Vec<PathBuf> {
    let mut sources = Vec::new();
    let mut stack = vec![shader_dir.to_path_buf()];

    while let Some(dir) = stack.pop() {
        let entries = fs::read_dir(&dir)
            .unwrap_or_else(|_| panic!("Failed to read shader directory: {}", dir.display()));

        for entry in entries {
            let entry = entry.unwrap_or_else(|_| panic!("Failed to read directory entry in {}", dir.display()));
            let path = entry.path();
            if path.is_dir() {
                stack.push(path);
                continue;
            }

            if path.is_file() && shader_kind_for_path(&path).is_some() {
                sources.push(path);
            }
        }
    }

    sources.sort();
    sources
}

fn discover_hlsl_sources(shader_dir: &Path) -> Vec<PathBuf> {
    if !shader_dir.exists() {
        return Vec::new();
    }

    let mut sources = Vec::new();
    let mut stack = vec![shader_dir.to_path_buf()];

    while let Some(dir) = stack.pop() {
        let entries = fs::read_dir(&dir)
            .unwrap_or_else(|_| panic!("Failed to read HLSL shader directory: {}", dir.display()));

        for entry in entries {
            let entry = entry.unwrap_or_else(|_| panic!("Failed to read directory entry in {}", dir.display()));
            let path = entry.path();
            if path.is_dir() {
                stack.push(path);
                continue;
            }

            if path.is_file() && hlsl_profile_for_path(&path).is_some() {
                sources.push(path);
            }
        }
    }

    sources.sort();
    sources
}

fn output_shader_artifact_name(shader_root: &Path, source_path: &Path) -> String {
    let relative = source_path.strip_prefix(shader_root).unwrap_or(source_path);
    let relative_norm = relative.to_string_lossy().replace('\\', "/");

    if relative_norm.contains('/') {
        format!("{}.spv", relative_norm.replace('/', "__"))
    } else {
        format!("{relative_norm}.spv")
    }
}

fn shader_kind_for_path(path: &Path) -> Option<shaderc::ShaderKind> {
    let file_name = path.file_name()?.to_str()?.to_ascii_lowercase();

    if file_name.ends_with(".vert") || file_name.ends_with(".vert.glsl") {
        return Some(shaderc::ShaderKind::Vertex);
    }
    if file_name.ends_with(".frag") || file_name.ends_with(".frag.glsl") {
        return Some(shaderc::ShaderKind::Fragment);
    }
    if file_name.ends_with(".comp") || file_name.ends_with(".comp.glsl") {
        return Some(shaderc::ShaderKind::Compute);
    }
    if file_name.ends_with(".geom") || file_name.ends_with(".geom.glsl") {
        return Some(shaderc::ShaderKind::Geometry);
    }
    if file_name.ends_with(".tesc") || file_name.ends_with(".tesc.glsl") {
        return Some(shaderc::ShaderKind::TessControl);
    }
    if file_name.ends_with(".tese") || file_name.ends_with(".tese.glsl") {
        return Some(shaderc::ShaderKind::TessEvaluation);
    }
    if file_name.ends_with(".rgen") || file_name.ends_with(".rgen.glsl") {
        return Some(shaderc::ShaderKind::RayGeneration);
    }
    if file_name.ends_with(".rahit") || file_name.ends_with(".rahit.glsl") {
        return Some(shaderc::ShaderKind::AnyHit);
    }
    if file_name.ends_with(".rchit") || file_name.ends_with(".rchit.glsl") {
        return Some(shaderc::ShaderKind::ClosestHit);
    }
    if file_name.ends_with(".rmiss") || file_name.ends_with(".rmiss.glsl") {
        return Some(shaderc::ShaderKind::Miss);
    }
    if file_name.ends_with(".rint") || file_name.ends_with(".rint.glsl") {
        return Some(shaderc::ShaderKind::Intersection);
    }
    if file_name.ends_with(".rcall") || file_name.ends_with(".rcall.glsl") {
        return Some(shaderc::ShaderKind::Callable);
    }
    if file_name.ends_with(".task") || file_name.ends_with(".task.glsl") {
        return Some(shaderc::ShaderKind::Task);
    }
    if file_name.ends_with(".mesh") || file_name.ends_with(".mesh.glsl") {
        return Some(shaderc::ShaderKind::Mesh);
    }

    None
}

fn hlsl_profile_for_path(path: &Path) -> Option<&'static str> {
    let file_name = path.file_name()?.to_str()?.to_ascii_lowercase();

    if file_name.ends_with(".vert.hlsl") {
        return Some("vs_6_0");
    }
    if file_name.ends_with(".frag.hlsl") {
        return Some("ps_6_0");
    }
    if file_name.ends_with(".comp.hlsl") {
        return Some("cs_6_0");
    }

    None
}
