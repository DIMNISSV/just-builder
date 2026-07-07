import ast
import os
import sys
from typing import List

from just_builder.utils.discovery import is_module_available


def get_third_party_imports(modules_list: List[str], orig_src: str, ignored_packages: List[str]) -> List[str]:
    discovered_imports = set()
    for mod in modules_list:
        path_parts = mod.split('.')
        py_file = os.path.join(orig_src, *path_parts) + ".py"

        if os.path.exists(py_file):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=py_file)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            discovered_imports.add(name.name)
                    elif isinstance(node, ast.ImportFrom):
                        level = getattr(node, 'level', 0) or 0
                        if level == 0 and node.module:
                            discovered_imports.add(node.module)
            except Exception as e:
                print(f"Warning: Failed to parse imports from {py_file}: {e}")

    ignored = set(ignored_packages)

    std_and_builtins = set(sys.builtin_module_names)
    if hasattr(sys, "stdlib_module_names"):
        std_and_builtins.update(sys.stdlib_module_names)

    filtered = set()
    for imp in discovered_imports:
        top_pkg = imp.split('.')[0]
        if top_pkg in ignored or top_pkg in std_and_builtins:
            continue
        if is_module_available(top_pkg):
            filtered.add(imp)
        else:
            print(f"Warning: Skipping unavailable dependency discovered in AST parser: {imp}")

    return sorted(list(filtered))
