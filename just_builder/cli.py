import argparse
import sys

from just_builder.config import BuildConfig
from just_builder.builder import Builder


def main():
    parser = argparse.ArgumentParser(
        description="Build script for JustDubberMatcher with Cython compile and PyInstaller."
    )
    parser.add_argument("--clean", action="store_true",
                        help="Delete build/, dist/ and spec files after successful compilation")
    parser.add_argument("--onefile", action="store_true", help="Package application into a single executable file")
    parser.add_argument("--console", action="store_true", help="Keep console window visible on runtime")
    parser.add_argument("--icon", type=str, default=None, help="Path to system icon file")
    parser.add_argument("--cpu", action="store_true", help="Build CPU-only variant")
    parser.add_argument("--gpu", action="store_true", help="Build standard GPU-enabled variant")
    parser.add_argument("--gpu-full", action="store_true",
                        help="Build self-contained GPU variant with CUDA/cuDNN binaries included")
    parser.add_argument("--password", type=str, default=None, help="Password to protect the generated SFX archive")
    parser.add_argument("--release", action="store_true",
                        help="Automatically move final SFX package into project's releases/ folder")
    parser.add_argument("--freeze", action="store_true",
                        help="Freeze (backup) original source files into a dedicated directory")
    parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Additional arguments passed to PyInstaller")

    args = parser.parse_args()

    config = BuildConfig(
        clean=args.clean,
        onefile=args.onefile,
        console=args.console,
        icon=args.icon,
        cpu=args.cpu,
        gpu=args.gpu,
        gpu_full=args.gpu_full,
        password=args.password,
        release=args.release,
        freeze=args.freeze,
        extra_args=args.extra_args
    )

    try:
        builder = Builder(config)
        builder.run()
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
