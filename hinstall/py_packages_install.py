import os
from pathlib import Path
import subprocess
import sys
from .logger import ilog
from .backend_dirs import g_backend_dirs



g_backend_env = None

def generate_backend_env(
    exclude: list[str] | None = None,
    exclude_append: list[str] | None = None,
) -> dict | None:
    global g_backend_env
    try:
        backend_env = _generate_backend_env(
            exclude=exclude,
            exclude_append=exclude_append
        )
        if backend_env is None:
            ilog.critical("Backend env generation returned None (unexpected).")
            return None
        g_backend_env = backend_env
        return backend_env

    except Exception as e:
        ilog.critical(f"Failed to define the backend environment: {str(e)}")
        return None

    return backend_env



def _generate_backend_env(
    exclude: list[str] | None = None,
    exclude_append: list[str] | None = None,
) -> dict:
    # Environnment
    # ilog.info(f"Local environment:")
    # ilog.info(get_python_env())

    if exclude is None:
        forbidden_names: list[str] = [
            'python',
            'conda',
            'vapoursynth',
            'windowsapps',
            'miniconda',
        ]
    else:
        forbidden_names = exclude

    if exclude_append is not None:
        forbidden_names.extend(exclude_append)

    python_dir: Path = g_backend_dirs.python_exe.parent
    if sys.platform == 'linux':
        python_dir = python_dir.parent
        sep: str = ":"

    elif sys.platform == "win32":
        sep: str = ";"

    # Clean the environment
    backend_env = os.environ.copy()

    # Explicitly clear the PATH
    original_path = os.environ.get('PATH', '')
    if 'PATH' in backend_env:
        del backend_env['PATH']

    for k, v in os.environ.items():
        if k == '_' or k not in backend_env:
            continue

        k_lower, v_lower = k.lower(), v.lower()
        for n in forbidden_names:
            if n in k_lower or n in v_lower:
                if k not in backend_env:
                    continue
                try:
                    del backend_env[k]
                    # ilog.debug(f"Removed: {k} = {v}")
                except KeyError as e:
                    ilog.debug(f"failed to remove {k}: {str(e)}")

    # Set new PATH
    path_entries = original_path.split(sep)
    filtered_path_entries = []
    for entry in path_entries:
        if entry == '.':
            continue

        entry_lower = entry.lower()
        is_forbidden = False
        for n in forbidden_names:
            if n in entry_lower:
                # ilog.debug(f"Removed path entry: {entry} (contains '{n}')")
                is_forbidden = True
                break

        if not is_forbidden and entry:
            filtered_path_entries.append(entry)

    backend_env['PATH'] = sep.join(
        [
            str(g_backend_dirs.python_exe.parent),
            str(g_backend_dirs.python_exe.parent / "Scripts"),
        ] + filtered_path_entries
    )

    python_exe = str(g_backend_dirs.python_exe)
    embedded_script = (Path(__file__).parent / "standalone_check.py").resolve()
    try:
        result = subprocess.run(
            [python_exe, embedded_script],
            capture_output=True,
            text=True,
            env=backend_env,
        )
        if not result.stdout.strip():
            ilog.critical("Failed to set the standalone environment")
        # ilog.debug(f"Embedded environment:")
        # ilog.debug(result.stdout)
        # print(result.stdout)
    except Exception as e:
        ilog.error(f"Environment check failed: {e}")

    return backend_env



def get_python_version(python_exe: Path | None = None) -> str:
    if True:
        # Get from subprocess to get the full version. Is this needed?
        version: str = ""

        python_exe = str(g_backend_dirs.python_exe if python_exe is None else python_exe)
        try:
            result = subprocess.run(
                [python_exe, '--version'],
                capture_output=True,
                text=True,
                env=g_backend_env
            )
            version = result.stdout.strip()
        except:
            pass
        return version

    else:
        return f"{sys.version_info.major}.{sys.version_info.minor}"



def update_pip(python_exe: Path | None = None) -> bool:
    python_exe = str(g_backend_dirs.python_exe if python_exe is None else python_exe)

    pip_command: str = f"{python_exe} -m pip install --upgrade pip"
    try:
        result = subprocess.run(
            pip_command.split(' '),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
            check=True,
            text=True,
            env=g_backend_env,
        )

    except subprocess.CalledProcessError as e:
        # Specific error if subprocess fails
        ilog.error(f"Error occurred while updating pip: {str(e)}")
        return False

    except Exception as e:
        # Catch all other unexpected errors
        ilog.error(f"Unexpected error: {str(e)}")
        return False

    ilog.debug(result.stdout.strip())
    return True



def get_pypackage_list(python_exe: Path | None = None) -> str:
    result_str: str = ""

    python_exe = str(g_backend_dirs.python_exe if python_exe is None else python_exe)
    pip_command: str = f"{python_exe} -m pip list"
    try:
        result = subprocess.run(
            pip_command.split(' '),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
            check=True,
            text=True,
            env=g_backend_env,
        )
        result_str = result.stdout.strip()
        ilog.debug(result_str)

    except subprocess.CalledProcessError as e:
        # Specific error if subprocess fails
        ilog.error(f"Error occurred while updating pip: {str(e)}")

    except Exception as e:
        # Catch all other unexpected errors
        ilog.error(f"Unexpected error: {str(e)}")

    return result_str


