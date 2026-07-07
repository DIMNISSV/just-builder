import os
import subprocess
from typing import List


def run_pyinstaller(
        temp_src: str,
        temp_launcher: str,
        build_root: str,
        dist_dir: str,
        onefile: bool,
        console: bool,
        icon: str,
        extra_args: List[str]
) -> None:
    translations_src = os.path.join(temp_src, 'just_dubber_gui', 'translations')
    translations_dest = "just_dubber_gui/translations"

    pyinstaller_cmd = ["pyinstaller", "--noconfirm"]

    if onefile:
        pyinstaller_cmd.append("--onefile")
    else:
        pyinstaller_cmd.append("--onedir")

    if console:
        pyinstaller_cmd.append("--console")
    else:
        pyinstaller_cmd.append("--windowed")

    if icon:
        if os.path.exists(icon):
            pyinstaller_cmd.extend(["--icon", icon])
        else:
            print(f"Warning: Icon file '{icon}' not found. Continuing build without icon.")

    pyinstaller_cmd.extend([
        "--name", "launcher",
        "--paths", temp_src,
        "--collect-all", "onnxruntime",
        "--collect-submodules", "just_dubber_matcher",
        "--collect-submodules", "just_dubber_gui",
        "--add-data", f"{translations_src}{os.pathsep}{translations_dest}",
        "--workpath", os.path.join(build_root, "pyi_work"),
        "--specpath", build_root,
        "--distpath", dist_dir,
    ])

    if extra_args:
        clean_extra = [arg for arg in extra_args if arg != "--"]
        pyinstaller_cmd.extend(clean_extra)

    pyinstaller_cmd.append(temp_launcher)

    print(f"Executing command: {' '.join(pyinstaller_cmd)}")
    result_pyi = subprocess.run(pyinstaller_cmd)
    if result_pyi.returncode != 0:
        raise RuntimeError("PyInstaller process failed.")
