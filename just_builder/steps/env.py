import os
import shutil
import subprocess
import sys
from typing import List


def setup_dependencies(cpu_build: bool, build_type: str, onnx_version: str) -> None:
    target_package = f"onnxruntime=={onnx_version}" if cpu_build else f"onnxruntime-gpu=={onnx_version}"
    to_uninstall = "onnxruntime-gpu" if cpu_build else "onnxruntime"

    print(f"\n=== Dynamic Dependency Setup for {build_type.upper()} ===")
    print(f"Uninstalling conflicting package if exists: {to_uninstall}")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", to_uninstall],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"Installing correct target package: {target_package}")
    result = subprocess.run([sys.executable, "-m", "pip", "install", target_package])
    if result.returncode != 0:
        print(f"Warning: Failed to install target package {target_package}. Proceeding with existing environment.")
    else:
        print(f"Dependency {target_package} configured successfully.")


def copy_cuda_cudnn_binaries(target_dir: str, cuda_paths: List[str], cudnn_paths: List[str]) -> None:
    print("\n=== Copying CUDA and cuDNN libraries to target folder ===")
    copied_files_count = 0

    cuda_src_dir = next((path for path in cuda_paths if os.path.exists(path)), None)
    if cuda_src_dir:
        print(f"Found CUDA binary directory: {cuda_src_dir}")
        for filename in os.listdir(cuda_src_dir):
            if filename.lower().endswith(('.dll', '.exe')):
                src_path = os.path.join(cuda_src_dir, filename)
                dst_path = os.path.join(target_dir, filename)
                if os.path.isfile(src_path):
                    try:
                        shutil.copy2(src_path, dst_path)
                        copied_files_count += 1
                    except Exception as e:
                        print(f"Could not copy {filename}: {e}")
    else:
        print("Warning: CUDA directory was not found in standard paths.")

    cudnn_src_dir = next((path for path in cudnn_paths if os.path.exists(path)), None)
    if cudnn_src_dir:
        print(f"Found cuDNN binary directory: {cudnn_src_dir}")
        for filename in os.listdir(cudnn_src_dir):
            if filename.lower().endswith(('.dll', '.exe')):
                src_path = os.path.join(cudnn_src_dir, filename)
                dst_path = os.path.join(target_dir, filename)
                if os.path.isfile(src_path):
                    try:
                        shutil.copy2(src_path, dst_path)
                        copied_files_count += 1
                    except Exception as e:
                        print(f"Could not copy {filename}: {e}")
    else:
        print("Warning: cuDNN directory was not found in standard paths.")

    print(f"Copied {copied_files_count} binary files from system GPU runtime paths.")
