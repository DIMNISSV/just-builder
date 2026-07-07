import os
import shutil
import sys
from typing import Optional


def find_7z() -> Optional[str]:
    for cmd in ["7z", "7za"]:
        path = shutil.which(cmd)
        if path:
            return path
    if sys.platform == "win32":
        common_windows_paths = [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
        ]
        for path in common_windows_paths:
            if os.path.exists(path):
                return path
    return None
