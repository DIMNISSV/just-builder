import datetime
import os
import shutil
import sys

from just_builder.config import BuildConfig
from just_builder.workspace import Workspace
from just_builder.utils.ast_parser import get_third_party_imports
from just_builder.utils.project_info import get_version_from_pyproject, get_platform_name
from just_builder.utils.system import find_7z
from just_builder.utils.discovery import discover_modules, get_top_level_packages
from just_builder.steps.env import setup_dependencies, copy_cuda_cudnn_binaries
from just_builder.steps.compiler import generate_setup_file, run_cython, clean_cython_sources
from just_builder.steps.packager_pyinstaller import run_pyinstaller
from just_builder.steps.packager_nuitka import run_nuitka
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
        dist_dir = os.path.join("dist", f"run_{run_suffix}")

        workspace = Workspace(self.config, build_root, dist_source_dir, dist_dir)

        if self.config.freeze:
            workspace.freeze_sources(run_suffix)

        is_cpu = self.config.cpu
        is_gpu_full = self.config.gpu_full
        is_gpu = self.config.gpu or (not is_cpu and not is_gpu_full)
        build_type = "cpu" if is_cpu else ("gpu-full" if is_gpu_full else "gpu")

        setup_dependencies(is_cpu, build_type, self.config.onnx_version)

        print("\n=== Setting up source directory ===")
        temp_src = workspace.prepare_temp_src()

        print("=== Extracting dependency tree ===")
        dependencies = get_third_party_imports(
            self.config.modules_to_compile,
            self.config.orig_src,
            self.config.ignored_packages
        )
        print(f"Identified external dependencies in compiled files: {dependencies}")

        temp_setup = os.path.join(dist_source_dir, "setup_temp.py")

        if self.config.backend == "pyinstaller":
            print("=== Compiling Cython modules inside intermediate folder ===")
            generate_setup_file(temp_setup, self.config.modules_to_compile, self.config.orig_src)
            run_cython(temp_setup, dist_source_dir)

            print("=== Removing original python files from intermediate folder ===")
            clean_cython_sources(temp_src, self.config.modules_to_compile, temp_setup)
        else:
            print(f"=== Skipping Cython compilation (Backend: {self.config.backend}) ===")

        print("=== Preparing temporary launcher ===")
        temp_launcher = os.path.join(build_root, "launcher_patched.py")
        shutil.copy2(self.config.launcher, temp_launcher)

        if self.config.backend == "pyinstaller":
            with open(temp_launcher, "a", encoding="utf-8") as f:
                f.write("\n\nif False:\n")
                for imp in dependencies:
                    f.write(f"    import {imp}\n")

            print("=== Packaging via PyInstaller ===")
            run_pyinstaller(
                temp_src=temp_src,
                launcher_path=temp_launcher,
                executable_name=self.config.executable_name,
                build_root=build_root,
                dist_dir=dist_dir,
                onefile=self.config.onefile,
                console=self.config.console,
                icon=self.config.icon,
                extra_args=self.config.extra_args,
                add_data=self.config.add_data,
                collect_all=self.config.collect_all,
                collect_submodules=self.config.collect_submodules,
                hidden_imports=self.config.hidden_imports,
                auto_dependencies=dependencies
            )
        elif self.config.backend == "nuitka":
            print("=== Packaging via Nuitka ===")
            run_nuitka(
                temp_src=temp_src,
                launcher_path=temp_launcher,
                executable_name=self.config.executable_name,
                build_root=build_root,
                dist_dir=dist_dir,
                onefile=self.config.onefile,
                console=self.config.console,
                icon=self.config.icon,
                extra_args=self.config.extra_args,
                add_data=self.config.add_data,
                collect_all=self.config.collect_all,
                collect_submodules=self.config.collect_submodules,
                hidden_imports=self.config.hidden_imports,
                auto_dependencies=dependencies
            )
        else:
            raise ValueError(f"Unknown packaging backend: {self.config.backend}")

        version = get_version_from_pyproject()
        full_version = f"{version}+{timestamp}"
        target_dir = os.path.join(dist_dir, f"{self.config.project_name}-{full_version}")

        print(f"=== Structuring final dist directory for version {full_version} ===")
        workspace.structure_dist_directory(target_dir)

        if is_gpu_full:
            copy_cuda_cudnn_binaries(target_dir, self.config.cuda_paths, self.config.cudnn_paths)

        platform_name = get_platform_name()
        archive_name = f"{self.config.project_name}-{full_version}-{platform_name}-{build_type}.exe"
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
                seven_zip_path, archive_name, f"{self.config.project_name}-{full_version}",
                dist_dir, self.config.password
            )
            if sfx_generated:
                print(f"SFX package generated successfully: {archive_path}")
        else:
            print("\n=== Warning: 7z binary was not found ===")
            print("SFX packaging step has been skipped.")

        if self.config.release and sfx_generated:
            workspace.move_to_release(archive_path, archive_name)

        if self.config.clean:
            workspace.cleanup(target_dir, archive_name, sfx_generated)

        print("\n=== Compilation and build successfully finalized ===")
