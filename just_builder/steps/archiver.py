import os
import subprocess
from typing import Optional


def create_sfx_archive(
        seven_zip_path: str,
        archive_name: str,
        target_folder_name: str,
        dist_dir: str,
        password: Optional[str]
) -> bool:
    seven_zip_dir = os.path.dirname(seven_zip_path)
    gui_sfx_path = os.path.join(seven_zip_dir, "7z.sfx")

    sfx_arg = "-sfx"
    if os.path.exists(gui_sfx_path):
        sfx_arg = f"-sfx{gui_sfx_path}"
        print(f"GUI SFX Module selected to enable extraction path prompt: {gui_sfx_path}")
    else:
        print("Warning: 7z.sfx GUI module not found. Falling back to default console extraction.")

    sfx_cmd = [seven_zip_path, "a", sfx_arg]

    if password:
        sfx_cmd.append(f"-p{password}")
        print("SFX archive will be encrypted with the provided password.")

    sfx_cmd.extend([archive_name, target_folder_name])

    print(f"Executing packaging: {' '.join(sfx_cmd)} in folder {dist_dir}")
    try:
        res = subprocess.run(sfx_cmd, cwd=dist_dir, capture_output=True, text=True)
        if res.returncode == 0:
            return True
        else:
            print(f"7z packaging error. Exit code: {res.returncode}")
            print(f"Console Output:\n{res.stdout}\n{res.stderr}")
            return False
    except Exception as e:
        print(f"Exception during SFX packaging process: {e}")
        return False
