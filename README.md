# Just Builder

Just Builder is a comprehensive build automation tool designed to orchestrate Cython compilation and PyInstaller packaging. It provides dynamic dependency management, source code freezing, and Self-Extracting (SFX) 7z archive generation.

## Installation

You can install the package directly from the GitHub repository. 

### Using Poetry

If your target project uses Poetry for dependency management, add `just-builder` to your development dependencies:

```bash
poetry add --group dev git+https://github.com/DIMNISSV/just-builder.git
```

### Using pip

If you are using a standard virtual environment:

```bash
pip install git+https://github.com/DIMNISSV/just-builder.git
```

## Usage

The package provides two primary ways to initiate the build process: via the Command Line Interface (CLI) or programmatically via the Python API.

### Command Line Interface (CLI)

Once installed, the `just-builder` executable becomes available in your environment. You can run it from the root directory of your target project.

Example of a standard GPU build with post-compilation cleanup:

```bash
just-builder --gpu --clean
```

Example of creating a single-file executable for CPU, preserving the console window, and outputting to a specific release folder:

```bash
just-builder --cpu --onefile --console --release --clean
```

#### CLI Arguments

*   `--clean` : Delete intermediate build, dist, and spec files after successful compilation.
*   `--onefile` : Package the application into a single executable file.
*   `--console` : Keep the console window visible during runtime.
*   `--icon <path>` : Path to a system icon file (.ico) to attach to the executable.
*   `--cpu` : Build the CPU-only variant (dynamically installs `onnxruntime`).
*   `--gpu` : Build the standard GPU-enabled variant (dynamically installs `onnxruntime-gpu`).
*   `--gpu-full` : Build a self-contained GPU variant with system CUDA and cuDNN binaries included.
*   `--password <pass>` : Password to protect and encrypt the generated SFX archive.
*   `--release` : Automatically move the final SFX package into the project's `releases/` directory.
*   `--freeze` : Backup original source files into a dedicated directory inside `build/` before starting.
*   `[extra_args]` : Any trailing arguments are passed directly to PyInstaller.

### Python API

For more granular control, you can import `just_builder` into a custom build script inside your target project. 

Create a file named `build_script.py` in your project root:

```python
from just_builder import BuildConfig, Builder

def main():
    config = BuildConfig(
        clean=True,
        gpu=True,
        release=True,
        onefile=False,
        console=False,
        orig_src="src",
        launcher="launcher.py",
        modules_to_compile=[
            "just_dubber_matcher.license",
            "just_dubber_gui.dialogs.license_dialog",
            "just_dubber_gui.controllers.main_controller",
            "just_dubber_matcher.project.project",
            "just_dubber_matcher.project.episode",
            "just_dubber_matcher.project.parsers",
            "just_dubber_matcher.exporter",
            "just_dubber_matcher.config",
            "just_dubber_matcher.api.facade",
            "just_dubber_matcher.models.clustering",
        ]
    )

    builder = Builder(config)
    builder.run()

if __name__ == "__main__":
    main()
```

Run your custom script:

```bash
python build_script.py
```

## Build Process Structure

1. **Environment Setup**: Dynamically installs required versions of `onnxruntime` or `onnxruntime-gpu` based on the configuration.
2. **Source Preparation**: Extracts the third-party dependency tree using AST parsing to ensure PyInstaller includes necessary hidden imports.
3. **Cython Compilation**: Generates C extensions for the specified modules and compiles them in-place, removing the original Python source files to protect intellectual property.
4. **PyInstaller Packaging**: Wraps the compiled extensions and assets into an executable or distribution folder.
5. **Archive Generation**: Utilizes system 7z binaries to pack the distribution into a Self-Extracting (SFX) archive. Includes an option for AES-256 encryption.
6. **Cleanup**: Discards temporary build artifacts and directories based on user parameters.
