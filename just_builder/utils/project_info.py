import os
import platform
import re
import sys


def get_version_from_pyproject(pyproject_path: str = "pyproject.toml") -> str:
    version = "0.1.0"
    if os.path.exists(pyproject_path):
        try:
            try:
                import tomllib
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                if "project" in data and "version" in data["project"]:
                    return data["project"]["version"]
                if "tool" in data and "poetry" in data["tool"] and "version" in data["tool"]["poetry"]:
                    return data["tool"]["poetry"]["version"]
            except ImportError:
                pass

            with open(pyproject_path, "r", encoding="utf-8") as f:
                content = f.read()
            matches = re.findall(r'^\s*version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
            if matches:
                return matches[0]
        except Exception as e:
            print(f"Warning: Failed to read version from {pyproject_path}: {e}")
    return version


def get_platform_name() -> str:
    system = sys.platform
    if system == "win32":
        platform_str = "windows"
    elif system == "darwin":
        platform_str = "macos"
    elif system.startswith("linux"):
        platform_str = "linux"
    else:
        platform_str = system

    arch = platform.machine().lower()
    if arch in ["amd64", "x86_64"]:
        arch = "x64"
    elif arch in ["i386", "i686", "x86"]:
        arch = "x86"
    elif arch in ["aarch64", "arm64"]:
        arch = "arm64"

    return f"{platform_str}-{arch}"
