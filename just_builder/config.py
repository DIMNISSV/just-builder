import dataclasses
from typing import List, Optional


@dataclasses.dataclass
class BuildConfig:
    clean: bool = False
    onefile: bool = False
    console: bool = False
    icon: Optional[str] = None
    cpu: bool = False
    gpu: bool = False
    gpu_full: bool = False
    password: Optional[str] = None
    release: bool = False
    freeze: bool = False
    extra_args: List[str] = dataclasses.field(default_factory=list)
    project_name: str = "project"
    executable_name: str = "launcher"
    orig_src: str = "src"
    launcher: str = "launcher.py"
    onnx_version: str = "1.27.0"
    cuda_paths: List[str] = dataclasses.field(default_factory=lambda: [
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\x64",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin"
    ])
    cudnn_paths: List[str] = dataclasses.field(default_factory=lambda: [
        r"C:\Program Files\NVIDIA\CUDNN\v9.24\bin\13.3\x64",
        r"C:\Program Files\NVIDIA\CUDNN\v8.9\bin"
    ])

    # Списки исключений и импортов
    exclude_modules: List[str] = dataclasses.field(default_factory=list)
    modules_to_compile: Optional[List[str]] = None
    ignored_packages: Optional[List[str]] = None
    add_data: List[str] = dataclasses.field(default_factory=list)
    collect_all: List[str] = dataclasses.field(default_factory=list)
    collect_submodules: List[str] = dataclasses.field(default_factory=list)
    hidden_imports: List[str] = dataclasses.field(default_factory=list)
