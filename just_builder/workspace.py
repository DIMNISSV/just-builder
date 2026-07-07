import os
import shutil
import sys

from just_builder.config import BuildConfig


class Workspace:
    def __init__(self, config: BuildConfig, build_root: str, dist_source_dir: str, dist_dir: str):
        self.config = config
        self.build_root = build_root
        self.dist_source_dir = dist_source_dir
        self.dist_dir = dist_dir

    def prepare_temp_src(self) -> str:
        if os.path.exists(self.dist_source_dir):
            shutil.rmtree(self.dist_source_dir)
        os.makedirs(self.dist_source_dir, exist_ok=True)
        temp_src = os.path.join(self.dist_source_dir, "src")
        ignore_patterns = shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyd', '*.pyo', '*.c')
        shutil.copytree(self.config.orig_src, temp_src, ignore=ignore_patterns)
        return temp_src

    def freeze_sources(self, run_suffix: str) -> None:
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

    def structure_dist_directory(self, target_dir: str) -> None:
        if os.path.exists(target_dir):
            try:
                shutil.rmtree(target_dir)
            except Exception as e:
                raise RuntimeError(f"Error cleaning target directory {target_dir}: {e}")

        exe_name = f"{self.config.executable_name}.exe" if sys.platform == "win32" else self.config.executable_name

        if self.config.onefile:
            source_exe = os.path.join(self.dist_dir, exe_name)
            if os.path.exists(source_exe):
                os.makedirs(target_dir, exist_ok=True)
                shutil.move(source_exe, os.path.join(target_dir, exe_name))
                print(f"Moved executable: {source_exe} -> {os.path.join(target_dir, exe_name)}")
            else:
                raise RuntimeError(f"Target executable {source_exe} was not found.")
        else:
            source_folder = os.path.join(self.dist_dir, self.config.executable_name)
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

    def move_to_release(self, archive_path: str, archive_name: str) -> None:
        releases_dir = "releases"
        os.makedirs(releases_dir, exist_ok=True)
        release_path = os.path.join(releases_dir, archive_name)
        if os.path.exists(archive_path):
            try:
                shutil.move(archive_path, release_path)
                print(f"SFX archive successfully moved to release directory: {release_path}")
            except Exception as e:
                print(f"Error: Failed to move package to releases/ directory: {e}")

    def cleanup(self, target_dir: str, archive_name: str, sfx_generated: bool) -> None:
        print("\n=== Executing Post-Compilation Cleanup ===")
        if os.path.exists(self.build_root):
            try:
                shutil.rmtree(self.build_root)
                print(f"Removed intermediate build directory: {self.build_root}/")
            except Exception as e:
                print(f"Warning: Failed to clear directory {self.build_root}/: {e}")

        archive_released = self.config.release and os.path.exists(os.path.join("releases", archive_name))
        archive_local = os.path.exists(os.path.join(self.dist_dir, archive_name))

        if sfx_generated and (archive_local or archive_released):
            if self.config.release:
                if os.path.exists(self.dist_dir):
                    try:
                        shutil.rmtree(self.dist_dir)
                        print(f"Removed temporary dist directory: {self.dist_dir}/")
                    except Exception as e:
                        print(f"Warning: Failed to clear directory {self.dist_dir}/: {e}")
            else:
                if os.path.exists(target_dir):
                    try:
                        shutil.rmtree(target_dir)
                        print(f"Removed unpacked target directory: {target_dir}/")
                    except Exception as e:
                        print(f"Warning: Failed to clear directory {target_dir}/: {e}")
        else:
            print("SFX archive was not finalized. Preserving compiled package folder within process dist/.")
