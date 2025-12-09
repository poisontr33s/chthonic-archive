#!/usr/bin/env python3
"""
Simple GPU Status Check - Honest Assessment

Shows EXACTLY what's working and what's not.
No lies, no "available but broken" nonsense.
"""

import sys
import subprocess

def run_cmd(cmd: list[str], timeout: int = 10) -> tuple[bool, str]:
    """Run command and return (success, output)."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def check_nvidia_driver() -> dict:
    """Check NVIDIA driver installation."""
    success, output = run_cmd(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"])
    if success:
        parts = output.strip().split(", ")
        return {
            "status": "✅ WORKING",
            "gpu_name": parts[0] if len(parts) > 0 else "Unknown",
            "driver": parts[1] if len(parts) > 1 else "Unknown",
            "memory": parts[2] if len(parts) > 2 else "Unknown",
        }
    return {"status": "❌ NOT WORKING", "error": output}

def check_cuda_toolkit() -> dict:
    """Check CUDA toolkit installation."""
    success, output = run_cmd(["nvcc", "--version"])
    if success:
        # Parse version from output
        for line in output.split("\n"):
            if "release" in line.lower():
                return {"status": "✅ WORKING", "version": line.strip()}
        return {"status": "✅ WORKING", "version": "Unknown"}
    return {"status": "❌ NOT WORKING", "error": "nvcc not found in PATH"}

def check_cudnn() -> dict:
    """Check cuDNN installation."""
    import os
    
    # Look for cuDNN DLLs
    cudnn_paths = []
    search_paths = [
        os.environ.get("CUDA_PATH", ""),
        r"C:\Program Files\NVIDIA\CUDNN",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA",
    ]
    
    for base in search_paths:
        if not base:
            continue
        for root, dirs, files in os.walk(base):
            for f in files:
                if f.startswith("cudnn") and f.endswith(".dll"):
                    cudnn_paths.append(os.path.join(root, f))
    
    if cudnn_paths:
        # Check which version
        for p in cudnn_paths:
            if "cudnn64_9" in p or "cudnn_9" in p:
                return {"status": "✅ WORKING", "version": "9.x", "path": p}
            elif "cudnn64_8" in p or "cudnn_8" in p:
                return {"status": "⚠️ WRONG VERSION", "version": "8.x (need 9.x)", "path": p}
        return {"status": "⚠️ FOUND BUT UNKNOWN VERSION", "paths": cudnn_paths[:3]}
    
    return {"status": "❌ NOT INSTALLED", "note": "cuDNN 9.x required for ONNX Runtime GPU"}

def check_onnx_runtime() -> dict:
    """Check ONNX Runtime and whether GPU actually works."""
    try:
        import onnxruntime as ort
    except ImportError:
        return {"status": "❌ NOT INSTALLED"}
    
    version = ort.__version__
    available = ort.get_available_providers()
    
    result = {
        "version": version,
        "listed_providers": available,
        "cpu": {"status": "✅ WORKING"},  # CPU always works
        "cuda": {"status": "❌ NOT WORKING"},
        "tensorrt": {"status": "❌ NOT WORKING"},
    }
    
    # Actually TEST if CUDA works by creating a session
    if "CUDAExecutionProvider" in available:
        try:
            import onnx
            from onnx import helper, TensorProto
            import numpy as np
            
            # Create minimal model
            A = helper.make_tensor_value_info('A', TensorProto.FLOAT, [2, 2])
            B = helper.make_tensor_value_info('B', TensorProto.FLOAT, [2, 2])
            C = helper.make_tensor_value_info('C', TensorProto.FLOAT, [2, 2])
            node = helper.make_node('MatMul', ['A', 'B'], ['C'])
            graph = helper.make_graph([node], 'test', [A, B], [C])
            model = helper.make_model(graph, opset_imports=[helper.make_opsetid('', 12)])
            model.ir_version = 8
            
            # Try to create session with CUDA ONLY (no fallback)
            sess = ort.InferenceSession(
                model.SerializeToString(),
                providers=['CUDAExecutionProvider']
            )
            active = sess.get_providers()
            
            if 'CUDAExecutionProvider' in active:
                result["cuda"]["status"] = "✅ WORKING"
            else:
                result["cuda"]["status"] = "❌ FAILS (falls back to CPU)"
                result["cuda"]["actual_providers"] = active
                
        except Exception as e:
            error_msg = str(e)
            if "cudnn" in error_msg.lower():
                result["cuda"]["status"] = "❌ MISSING cuDNN"
                result["cuda"]["error"] = "cuDNN 9.x not installed"
            else:
                result["cuda"]["status"] = "❌ ERROR"
                result["cuda"]["error"] = error_msg[:200]
    
    # Test TensorRT
    if "TensorrtExecutionProvider" in available:
        try:
            # Similar test but for TensorRT
            sess = ort.InferenceSession(
                model.SerializeToString(),
                providers=['TensorrtExecutionProvider']
            )
            active = sess.get_providers()
            if 'TensorrtExecutionProvider' in active:
                result["tensorrt"]["status"] = "✅ WORKING"
            else:
                result["tensorrt"]["status"] = "❌ FAILS"
        except Exception as e:
            if "nvinfer" in str(e).lower():
                result["tensorrt"]["status"] = "❌ MISSING TensorRT libs"
            else:
                result["tensorrt"]["status"] = "❌ ERROR"
    
    # Overall status
    if result["cuda"]["status"].startswith("✅") or result["tensorrt"]["status"].startswith("✅"):
        result["status"] = "✅ GPU ACCELERATION AVAILABLE"
    else:
        result["status"] = "⚠️ INSTALLED BUT GPU NOT WORKING"
    
    return result

def check_cupy() -> dict:
    """Check CuPy availability."""
    try:
        import cupy as cp
        device = cp.cuda.Device(0)
        props = cp.cuda.runtime.getDeviceProperties(0)
        return {
            "status": "✅ WORKING",
            "device": props["name"].decode() if isinstance(props["name"], bytes) else props["name"],
            "memory_gb": props["totalGlobalMem"] / (1024**3),
        }
    except ImportError:
        return {"status": "❌ NOT INSTALLED"}
    except Exception as e:
        return {"status": "❌ ERROR", "error": str(e)[:200]}

def main():
    print("=" * 60)
    print("  GPU STATUS - HONEST ASSESSMENT")
    print("=" * 60)
    print()
    
    # NVIDIA Driver
    print("  1. NVIDIA Driver")
    driver = check_nvidia_driver()
    print(f"     Status: {driver['status']}")
    if driver["status"].startswith("✅"):
        print(f"     GPU: {driver.get('gpu_name', 'N/A')}")
        print(f"     Driver: {driver.get('driver', 'N/A')}")
        print(f"     Memory: {driver.get('memory', 'N/A')}")
    print()
    
    # CUDA Toolkit
    print("  2. CUDA Toolkit")
    cuda = check_cuda_toolkit()
    print(f"     Status: {cuda['status']}")
    if cuda["status"].startswith("✅"):
        print(f"     Version: {cuda.get('version', 'N/A')}")
    print()
    
    # cuDNN
    print("  3. cuDNN Library")
    cudnn = check_cudnn()
    print(f"     Status: {cudnn['status']}")
    if "version" in cudnn:
        print(f"     Version: {cudnn['version']}")
    if "note" in cudnn:
        print(f"     Note: {cudnn['note']}")
    print()
    
    # ONNX Runtime
    print("  4. ONNX Runtime")
    onnx_result = check_onnx_runtime()
    print(f"     Status: {onnx_result.get('status', 'N/A')}")
    if "version" in onnx_result:
        print(f"     Version: {onnx_result['version']}")
        print(f"     CPU: {onnx_result['cpu']['status']}")
        print(f"     CUDA: {onnx_result['cuda']['status']}")
        if "error" in onnx_result["cuda"]:
            print(f"            → {onnx_result['cuda']['error']}")
        print(f"     TensorRT: {onnx_result['tensorrt']['status']}")
    print()
    
    # CuPy
    print("  5. CuPy")
    cupy = check_cupy()
    print(f"     Status: {cupy['status']}")
    if cupy["status"].startswith("✅"):
        print(f"     Device: {cupy.get('device', 'N/A')}")
        print(f"     Memory: {cupy.get('memory_gb', 0):.1f} GB")
    print()
    
    # Summary
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print()
    
    gpu_working = False
    
    if cupy["status"].startswith("✅"):
        print("  ✅ CuPy GPU acceleration is WORKING")
        gpu_working = True
    
    if onnx_result.get("cuda", {}).get("status", "").startswith("✅"):
        print("  ✅ ONNX CUDA acceleration is WORKING")
        gpu_working = True
    
    if onnx_result.get("tensorrt", {}).get("status", "").startswith("✅"):
        print("  ✅ ONNX TensorRT acceleration is WORKING")
        gpu_working = True
    
    if not gpu_working:
        print("  ❌ NO GPU ACCELERATION WORKING")
        print()
        print("  To fix ONNX Runtime GPU:")
        print("    1. Download cuDNN 9.x from NVIDIA Developer")
        print("    2. Extract to CUDA_PATH\\bin (add DLLs to PATH)")
        print("    3. Restart terminal and test again")
        print()
        print("  OR use CuPy instead:")
        print("    uv pip install cupy-cuda12x  (when available for your Python)")
    
    print()
    
    return 0 if gpu_working else 1

if __name__ == "__main__":
    sys.exit(main())
