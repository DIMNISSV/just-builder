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

    orig_src: str = "src"
    launcher: str = "launcher.py"

    exclude_modules: List[str] = dataclasses.field(default_factory=list)
    modules_to_compile: Optional[List[str]] = None
    ignored_packages: Optional[List[str]] = None
