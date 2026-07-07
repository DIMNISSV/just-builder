import os
import subprocess
import sys
from typing import List
from just_builder.utils.discovery import is_module_available


def run_pyinstaller(
        temp_src: str,
        launcher_path: str,
        executable_name: str,
        build_root: str,
        dist_dir: str,
        onefile: bool,
        console: bool,
        icon: str,
        extra_args: List[str],
        add_data: List[str],
        collect_all: List[str],
        collect_submodules: List[str],
        hidden_imports: List[str],
        auto_dependencies: List[str]
) -> None:
    pyinstaller_cmd = ["pyinstaller", "--noconfirm"]

    if onefile:
        pyinstaller_cmd.append("--onefile")
    else:
        pyinstaller_cmd.append("--onedir")

    if console:
        pyinstaller_cmd.append("--console")
    else:
        pyinstaller_cmd.append("--windowed")

    if icon and os.path.exists(icon):
        pyinstaller_cmd.extend(["--icon", os.path.abspath(icon)])

    pyinstaller_cmd.extend([
        "--name", executable_name,
        "--paths", os.path.abspath(temp_src),
        "--workpath", os.path.abspath(os.path.join(build_root, "pyi_work")),
        "--specpath", os.path.abspath(build_root),
        "--distpath", os.path.abspath(dist_dir),
    ])

    all_hidden = set(hidden_imports + auto_dependencies)
    for imp in all_hidden:
        if is_module_available(imp):
            pyinstaller_cmd.extend(["--hidden-import", imp])

    for ca in collect_all:
        if is_module_available(ca):
            pyinstaller_cmd.extend(["--collect-all", ca])

    for csub in collect_submodules:
        if is_module_available(csub):
            pyinstaller_cmd.extend(["--collect-submodules", csub])

    for data in add_data:
        separator = os.pathsep if os.pathsep in data else (";" if sys.platform == "win32" else ":")
        if separator in data:
            src, dest = data.split(separator, 1)
            abs_src = os.path.abspath(src)
            pyinstaller_cmd.extend(["--add-data", f"{abs_src}{separator}{dest}"])
        else:
            pyinstaller_cmd.extend(["--add-data", data])

    if extra_args:
        clean_extra = [arg for arg in extra_args if arg != "--"]
        pyinstaller_cmd.extend(clean_extra)

    pyinstaller_cmd.append(os.path.abspath(launcher_path))

    print(f"Executing command: {' '.join(pyinstaller_cmd)}")
    result_pyi = subprocess.run(pyinstaller_cmd)
    if result_pyi.returncode != 0:
        raise RuntimeError("PyInstaller process failed.")
