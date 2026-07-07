import os
import subprocess
import sys
import shutil
from typing import List
from just_builder.utils.discovery import is_module_available


def run_nuitka(
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
    cmd = [sys.executable, "-m", "nuitka", "--assume-yes-for-downloads"]

    if onefile:
        cmd.append("--onefile")
        cmd.append(f"--output-filename={executable_name}")
    else:
        cmd.append("--standalone")

    if not console:
        cmd.append("--disable-console")

    if icon and os.path.exists(icon):
        if sys.platform == "win32":
            cmd.append(f"--windows-icon-from-ico={os.path.abspath(icon)}")
        elif sys.platform == "darwin":
            cmd.append(f"--macos-app-icon={os.path.abspath(icon)}")

    cmd.append(f"--output-dir={os.path.abspath(build_root)}")

    all_hidden = set(hidden_imports + auto_dependencies)
    for imp in all_hidden:
        if is_module_available(imp):
            cmd.append(f"--include-module={imp}")
        else:
            print(f"Warning: Skipping unavailable module '{imp}' from Nuitka --include-module")

    all_pkgs = set(collect_all + collect_submodules)
    for pkg in all_pkgs:
        if is_module_available(pkg):
            cmd.append(f"--include-package={pkg}")
        else:
            print(f"Warning: Skipping unavailable package '{pkg}' from Nuitka --include-package")

    for data in add_data:
        separator = os.pathsep if os.pathsep in data else (";" if sys.platform == "win32" else ":")
        if separator in data:
            src, dest = data.split(separator, 1)
            abs_src = os.path.abspath(src)
            if os.path.isdir(abs_src):
                cmd.append(f"--include-data-dir={abs_src}={dest}")
            else:
                cmd.append(f"--include-data-files={abs_src}={dest}")
        else:
            abs_src = os.path.abspath(data)
            if os.path.isdir(abs_src):
                cmd.append(f"--include-data-dir={abs_src}={os.path.basename(abs_src)}")
            else:
                cmd.append(f"--include-data-files={abs_src}={os.path.basename(abs_src)}")

    if extra_args:
        clean_extra = [arg for arg in extra_args if arg != "--"]
        cmd.extend(clean_extra)

    cmd.append(os.path.abspath(launcher_path))

    env = os.environ.copy()
    parent_src = os.path.abspath(os.path.dirname(temp_src))
    env["PYTHONPATH"] = f"{os.path.abspath(temp_src)}{os.pathsep}{parent_src}{os.pathsep}{env.get('PYTHONPATH', '')}"

    print(f"Executing Nuitka command: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        raise RuntimeError("Nuitka process failed.")

    os.makedirs(dist_dir, exist_ok=True)
    launcher_name = os.path.splitext(os.path.basename(launcher_path))[0]

    if onefile:
        exe_name = executable_name
        if sys.platform == "win32" and not exe_name.endswith('.exe'):
            exe_name += ".exe"

        built_exe = os.path.join(build_root, exe_name)
        fallback_exe = os.path.join(build_root, launcher_name + (".exe" if sys.platform == "win32" else ".bin"))

        if not os.path.exists(built_exe) and os.path.exists(fallback_exe):
            built_exe = fallback_exe

        target_exe = os.path.join(dist_dir, exe_name)
        if os.path.exists(built_exe):
            shutil.move(built_exe, target_exe)
        else:
            raise RuntimeError(f"Nuitka output {built_exe} not found.")
    else:
        dist_folder = os.path.join(build_root, f"{launcher_name}.dist")
        target_folder = os.path.join(dist_dir, executable_name)
        if os.path.exists(dist_folder):
            shutil.move(dist_folder, target_folder)
        else:
            raise RuntimeError(f"Nuitka output folder {dist_folder} not found.")
