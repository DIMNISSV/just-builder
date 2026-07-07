import os
import subprocess
import sys
from typing import List


def generate_setup_file(setup_path: str, modules_to_compile: List[str], orig_src: str = "src") -> None:
    extensions_code = []
    for mod in modules_to_compile:
        path_parts = mod.split('.')
        src_path = f"{orig_src}/{'/'.join(path_parts)}.py"
        extensions_code.append(f'    Extension("{mod}", ["{src_path}"]),')

    extensions_str = "\n".join(extensions_code)
    setup_content = f"""from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
{extensions_str}
]

setup(
    package_dir={{"": "{orig_src}"}},
    ext_modules=cythonize(extensions, compiler_directives={{'language_level': "3"}}),
)
"""
    with open(setup_path, "w", encoding="utf-8") as f:
        f.write(setup_content)


def run_cython(setup_path: str, cwd: str) -> None:
    setup_filename = os.path.basename(setup_path)
    result = subprocess.run(
        [sys.executable, setup_filename, "build_ext", "--inplace"],
        cwd=cwd
    )
    if result.returncode != 0:
        raise RuntimeError("Cython compilation step failed.")


def clean_cython_sources(temp_src: str, modules_to_compile: List[str], setup_path: str) -> None:
    for mod in modules_to_compile:
        path_parts = mod.split('.')
        rel_py = os.path.join(*path_parts) + ".py"
        rel_c = os.path.join(*path_parts) + ".c"

        py_to_del = os.path.join(temp_src, rel_py)
        c_to_del = os.path.join(temp_src, rel_c)

        if os.path.exists(py_to_del):
            os.remove(py_to_del)
            print(f"Deleted source file: {py_to_del}")
        if os.path.exists(c_to_del):
            os.remove(c_to_del)

    if os.path.exists(setup_path):
        os.remove(setup_path)
