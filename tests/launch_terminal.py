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
        shell = os.environ.get("COMSPEC", "cmd.exe")
        clear_conda = (
            'set "CONDA_EXE=" & '
            'set "CONDA_EXES=" & '
            'set "CONDA_SHLVL=" & '
            'set "CONDA_PREFIX=" & '
            'set "CONDA_DEFAULT_ENV=" & '
            'set "CONDA_PROMPT_MODIFIER=" & '
            'set "_CE_CONDA=" & '
            'set "_CE_M=" & '
            'cls'
        )

        print(f"--- Launching standalone terminal ({shell}) ---")
        subprocess.run(
            [shell, "/D", "/K", clear_conda],
            env=backend_env,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
    else:
        # Linux/Mac: Use os.execvpe for full process replacement (best method)
        shell = os.environ.get("SHELL", "/bin/bash")

        # Add the -i (interactive) flag to the arguments
        # The first argument in the list is always the program name (usually the shell path itself)
        args = [shell, "--login", "--norc", "--noprofile"]

        print(f"--- Replacing Python process with standalone terminal ({shell}) ---")

        # os.execvpe replaces the current Python process with the shell
        # If this fails, it throws an exception (it doesn't return)
        try:
            os.execvpe(shell, args, env=backend_env)
        except OSError as e:
            print(f"🚨 Failed to execute shell: {e}")

    print("\n--- Exited standalone environment ---")

