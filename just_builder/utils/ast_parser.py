import ast
import os
from typing import List


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
                            top_pkg = name.name.split('.')[0]
                            if top_pkg:
                                discovered_imports.add(top_pkg)
                    elif isinstance(node, ast.ImportFrom):
                        level = getattr(node, 'level', 0) or 0
                        if level == 0 and node.module:
                            top_pkg = node.module.split('.')[0]
                            if top_pkg:
                                discovered_imports.add(top_pkg)
            except Exception as e:
                print(f"Warning: Failed to parse imports from {py_file}: {e}")

    ignored = set(ignored_packages)
    filtered = {imp for imp in discovered_imports if imp not in ignored}
    return sorted(list(filtered))
