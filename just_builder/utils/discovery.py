import os
import sys
import importlib.util
from typing import List


def is_module_available(name: str) -> bool:
    top_level = name.split('.')[0]
    if top_level in sys.builtin_module_names:
        return True
    if hasattr(sys, "stdlib_module_names") and top_level in sys.stdlib_module_names:
        return True
    try:
        return importlib.util.find_spec(top_level) is not None
    except Exception:
        return False


def discover_modules(src_dir: str, exclude_list: List[str]) -> List[str]:
    modules = []
    if not os.path.exists(src_dir):
        return modules

    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                rel_path = os.path.relpath(os.path.join(root, file), src_dir)
                module_name = rel_path.replace(os.sep, ".")[:-3]

                is_excluded = False
                for excl in exclude_list:
                    if module_name == excl or module_name.startswith(excl + "."):
                        is_excluded = True
                        break

                if not is_excluded:
                    modules.append(module_name)
    return sorted(modules)


def get_top_level_packages(src_dir: str) -> List[str]:
    packages = []
    if not os.path.exists(src_dir):
        return packages

    for item in os.listdir(src_dir):
        item_path = os.path.join(src_dir, item)
        if os.path.isdir(item_path) and item != "__pycache__":
            packages.append(item)
        elif os.path.isfile(item_path) and item.endswith(".py") and item != "__init__.py":
            packages.append(item[:-3])

    return packages
