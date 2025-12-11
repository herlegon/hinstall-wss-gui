import os
from pathlib import Path
from pprint import pprint
import sys
import subprocess

sys.path.append(str(Path(__file__).resolve().parent.parent))
from hinstall import (
    generate_backend_env,
    g_backend_env
)


if __name__ == "__main__":
    backend_env = generate_backend_env()


    # 1. Determine the shell and arguments
    if sys.platform == "win32":
        shell = "powershell.exe"
        clear_conda_ps = (
            "Remove-Item Env:CONDA_EXE -ErrorAction Ignore; "
            "Remove-Item Env:CONDA_EXES -ErrorAction Ignore; "
            "Remove-Item Env:CONDA_SHLVL -ErrorAction Ignore; "
            "Remove-Item Env:CONDA_PREFIX -ErrorAction Ignore; "
            "Remove-Item Env:CONDA_DEFAULT_ENV -ErrorAction Ignore; "
            "Remove-Item Env:CONDA_PROMPT_MODIFIER -ErrorAction Ignore; "
            "Remove-Item Env:_CE_CONDA -ErrorAction Ignore; "
            "Remove-Item Env:_CE_M -ErrorAction Ignore; "
            "Clear-Host;"
            'function prompt {"[hrl] " + $(Get-Location) + "> "};'
        )

        print(f"--- Launching standalone terminal ({shell}) ---")
        cmd = [shell, "-NoExit", "-Command", clear_conda_ps]
        subprocess.run(
            cmd,
            env=backend_env,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr
        )

    else:
        # Linux/Mac: Use os.execvpe for full process replacement (best method)
        shell = os.environ.get("SHELL", "/bin/bash")
        # args = [shell, "--login", "--norc", "--noprofile"]
        args = [shell]

        print(f"--- Replacing Python process with standalone terminal ({shell}) ---")

        # os.execvpe replaces the current Python process with the shell
        # If this fails, it throws an exception (it doesn't return)
        try:
            os.execvpe(shell, args, env=backend_env)
        except OSError as e:
            print(f"🚨 Failed to execute shell: {e}")

    print("\n--- Exited standalone environment ---")

