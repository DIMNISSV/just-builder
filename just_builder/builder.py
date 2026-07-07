import datetime
import os
import shutil
import sys

from just_builder.config import BuildConfig
from just_builder.utils.ast_parser import get_third_party_imports
from just_builder.utils.project_info import get_version_from_pyproject, get_platform_name
from just_builder.utils.system import find_7z
from just_builder.utils.discovery import discover_modules, get_top_level_packages
from just_builder.steps.env import setup_dependencies, copy_cuda_cudnn_binaries
from just_builder.steps.compiler import generate_setup_file, run_cython, clean_cython_sources
from just_builder.steps.packager import run_pyinstaller
from just_builder.steps.archiver import create_sfx_archive


class Builder:
    def __init__(self, config: BuildConfig):
        self.config = config
        self._initialize_discovery()

    def _initialize_discovery(self) -> None:
        if self.config.modules_to_compile is None:
            self.config.modules_to_compile = discover_modules(
                self.config.orig_src,
                self.config.exclude_modules
            )
            print(f"Auto-discovered {len(self.config.modules_to_compile)} modules to compile.")

        if self.config.ignored_packages is None:
            self.config.ignored_packages = get_top_level_packages(self.config.orig_src)
            print(f"Auto-discovered top-level packages to ignore in AST parser: {self.config.ignored_packages}")

    def run(self):
        if self.config.cpu and (self.config.gpu or self.config.gpu_full):
            raise ValueError("Cannot specify both --cpu and GPU build flags simultaneously.")

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        run_suffix = f"{timestamp}_{os.getpid()}"

        build_root = os.path.join("build", f"run_{run_suffix}")
        dist_source_dir = os.path.join(build_root, "dist_source")
        temp_src = os.path.join(dist_source_dir, "src")
        temp_launcher = os.path.join(dist_source_dir, "launcher.py")
        temp_setup = os.path.join(dist_source_dir, "setup_temp.py")
        dist_dir = os.path.join("dist", f"run_{run_suffix}")

        is_cpu = self.config.cpu
        is_gpu_full = self.config.gpu_full
        is_gpu = self.config.gpu or (not self.config.cpu and not self.config.gpu_full)

        build_type = "cpu" if is_cpu else ("gpu-full" if is_gpu_full else "gpu")

        if self.config.freeze:
            self._freeze_sources(run_suffix)

        setup_dependencies(is_cpu, build_type)

        print("\n=== Setting up source directory ===")
        if os.path.exists(dist_source_dir):
            shutil.rmtree(dist_source_dir)
        os.makedirs(dist_source_dir, exist_ok=True)

        print("=== Extracting dependency tree ===")
        dependencies = get_third_party_imports(
            self.config.modules_to_compile,
            self.config.orig_src,
            self.config.ignored_packages
        )
        print(f"Identified external dependencies in compiled files: {dependencies}")

        print("=== Copying project files to intermediate folder ===")
        ignore_patterns = shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyd', '*.pyo', '*.c')
        shutil.copytree(self.config.orig_src, temp_src, ignore=ignore_patterns)
        shutil.copyfile(self.config.launcher, temp_launcher)

        self._inject_dummy_imports(temp_launcher, dependencies)

        print("=== Generating setup_temp.py ===")
        generate_setup_file(temp_setup, self.config.modules_to_compile)

        print("=== Compiling Cython modules inside intermediate folder ===")
        run_cython(temp_setup, dist_source_dir)

        print("=== Removing original python files from intermediate folder ===")
        clean_cython_sources(temp_src, self.config.modules_to_compile, temp_setup)

        print("=== Packaging via PyInstaller ===")
        run_pyinstaller(
            temp_src, temp_launcher, build_root, dist_dir,
            self.config.onefile, self.config.console, self.config.icon, self.config.extra_args
        )

        version = get_version_from_pyproject()
        full_version = f"{version}+{timestamp}"
        target_dir = os.path.join(dist_dir, f"just-dubber-matcher-{full_version}")

        print(f"=== Structuring final dist directory for version {full_version} ===")
        self._structure_dist_directory(dist_dir, target_dir)

        if is_gpu_full:
            copy_cuda_cudnn_binaries(target_dir)

        platform_name = get_platform_name()
        archive_name = f"just-dubber-matcher-{full_version}-{platform_name}-{build_type}.exe"
        archive_path = os.path.join(dist_dir, archive_name)

        if os.path.exists(archive_path):
            try:
                os.remove(archive_path)
            except Exception as e:
                print(f"Warning: Failed to remove old archive {archive_path}: {e}")

        sfx_generated = False
        seven_zip_path = find_7z()
        if seven_zip_path:
            print(f"\n=== Creating Self-Extracting SFX Archive ({archive_name}) ===")
            sfx_generated = create_sfx_archive(
                seven_zip_path, archive_name, f"just-dubber-matcher-{full_version}",
                dist_dir, self.config.password
            )
            if sfx_generated:
                print(f"SFX package generated successfully: {archive_path}")
        else:
            print("\n=== Warning: 7z binary was not found ===")
            print("SFX packaging step has been skipped.")

        if self.config.release and sfx_generated:
            self._move_to_release(archive_path, archive_name)

        if self.config.clean:
            self._cleanup(build_root, dist_dir, target_dir, archive_name, sfx_generated)

        print("\n=== Compilation and build successfully finalized ===")

    def _freeze_sources(self, run_suffix: str) -> None:
        frozen_dir = os.path.join("build", f"frozen_src_{run_suffix}")
        print(f"\n=== Freezing original sources to {frozen_dir} ===")
        try:
            os.makedirs(frozen_dir, exist_ok=True)
            shutil.copytree(
                self.config.orig_src,
                os.path.join(frozen_dir, "src"),
                ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyd', '*.pyo', '*.c')
            )
            if os.path.exists(self.config.launcher):
                shutil.copy2(self.config.launcher, os.path.join(frozen_dir, self.config.launcher))
            if os.path.exists("pyproject.toml"):
                shutil.copy2("pyproject.toml", os.path.join(frozen_dir, "pyproject.toml"))
            print(f"Sources successfully frozen at: {frozen_dir}")
        except Exception as e:
            print(f"Warning: Failed to freeze source files: {e}")

    def _inject_dummy_imports(self, launcher_path: str, dependencies: list) -> None:
        dummy_imports_lines = [
            "\n# Dynamic dummy imports for PyInstaller analyzer",
            "if False:"
        ]
        for dep in dependencies:
            dummy_imports_lines.append(f"    import {dep}")
        dummy_imports = "\n".join(dummy_imports_lines) + "\n"
        with open(launcher_path, "a", encoding="utf-8") as f:
            f.write(dummy_imports)

    def _structure_dist_directory(self, dist_dir: str, target_dir: str) -> None:
        if os.path.exists(target_dir):
            try:
                shutil.rmtree(target_dir)
            except Exception as e:
                raise RuntimeError(f"Error cleaning target directory {target_dir}: {e}")

        exe_name = "launcher.exe" if sys.platform == "win32" else "launcher"

        if self.config.onefile:
            source_exe = os.path.join(dist_dir, exe_name)
            if os.path.exists(source_exe):
                os.makedirs(target_dir, exist_ok=True)
                shutil.move(source_exe, os.path.join(target_dir, exe_name))
                print(f"Moved executable: {source_exe} -> {os.path.join(target_dir, exe_name)}")
            else:
                raise RuntimeError(f"Target executable {source_exe} was not found.")
        else:
            source_folder = os.path.join(dist_dir, "launcher")
            if os.path.exists(source_folder):
                shutil.move(source_folder, target_dir)
                print(f"Moved output folder: {source_folder} -> {target_dir}")
            else:
                raise RuntimeError(f"Source directory {source_folder} was not found.")

        additional_files = ["LICENSE", "LICENSE.txt", "LICENSE.md", "README.md", "README.txt"]
        for filename in additional_files:
            if os.path.exists(filename):
                try:
                    shutil.copy(filename, target_dir)
                    print(f"Copied: {filename} -> {target_dir}")
                except Exception as e:
                    print(f"Warning: Failed to copy {filename}: {e}")

    def _move_to_release(self, archive_path: str, archive_name: str) -> None:
        releases_dir = "releases"
        os.makedirs(releases_dir, exist_ok=True)
        release_path = os.path.join(releases_dir, archive_name)
        if os.path.exists(archive_path):
            try:
                shutil.move(archive_path, release_path)
                print(f"SFX archive successfully moved to release directory: {release_path}")
            except Exception as e:
                print(f"Error: Failed to move package to releases/ directory: {e}")

    def _cleanup(self, build_root: str, dist_dir: str, target_dir: str, archive_name: str, sfx_generated: bool) -> None:
        print("\n=== Executing Post-Compilation Cleanup ===")
        if os.path.exists(build_root):
            try:
                shutil.rmtree(build_root)
                print(f"Removed intermediate build directory: {build_root}/")
            except Exception as e:
                print(f"Warning: Failed to clear directory {build_root}/: {e}")

        archive_released = self.config.release and os.path.exists(os.path.join("releases", archive_name))
        archive_local = os.path.exists(os.path.join(dist_dir, archive_name))

        if sfx_generated and (archive_local or archive_released):
            if self.config.release:
                if os.path.exists(dist_dir):
                    try:
                        shutil.rmtree(dist_dir)
                        print(f"Removed temporary dist directory: {dist_dir}/")
                    except Exception as e:
                        print(f"Warning: Failed to clear directory {dist_dir}/: {e}")
            else:
                if os.path.exists(target_dir):
                    try:
                        shutil.rmtree(target_dir)
                        print(f"Removed unpacked target directory: {target_dir}/")
                    except Exception as e:
                        print(f"Warning: Failed to clear directory {target_dir}/: {e}")
        else:
            print("SFX archive was not finalized. Preserving compiled package folder within process dist/.")
