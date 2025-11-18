import os
from pathlib import Path
from pprint import pprint
import sys
import subprocess

sys.path.append(str(Path(__file__).resolve().parent.parent))
from hinstall import (
    parse_packages_toml_,
    ExtPackages,
    PyPackages,
    g_backend_dirs,
    download_install_ext_packages,
    generate_backend_env,
    g_backend_env
)

# def launch_terminal_with_env():
    # 1. Get the sanitized environment


    # try:

    #     # 2. Determine the shell to launch based on OS
    #     if sys.platform == "win32":
    #             shell = os.environ.get("COMSPEC", "cmd.exe")
    #     else:
    #         shell = os.environ.get("SHELL", "/bin/bash")

    #     print(f"--- Launching standalone terminal ({shell}) ---")
    #     print(f"--- Type 'exit' to return to your normal environment ---")

    #     # 3. Run the shell with the new environment
    #     # We use subprocess.run to keep the python script waiting until the shell exits
    #     subprocess.run([shell], env=new_env)

    #     print("\n--- Exited standalone environment ---")

    # except Exception as e:
    #     print(f"Error launching terminal: {e}")

if __name__ == "__main__":
    generate_backend_env()
    pprint(g_backend_env)

    # 1. Determine the shell and arguments
    if sys.platform == "win32":
        shell = os.environ.get("COMSPEC", "cmd.exe")
        args = [shell]
        # On Windows, os.execvpe can be less reliable, stick to subprocess.
        # Ensure subprocess.run has basic input/output settings.
        print(f"--- Launching standalone terminal ({shell}) ---")
        subprocess.run(
            args,
            env=new_env,
            # Ensure proper handles are passed for interactivity
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
            os.execvpe(shell, args, env=g_backend_env)
        except OSError as e:
            print(f"🚨 Failed to execute shell: {e}")

    print("\n--- Exited standalone environment ---")

