from concurrent.futures import ThreadPoolExecutor
from hytils import lightcyan, lightgreen, orange, red, get_org_tempdir
from importlib import metadata
import os
from pathlib import Path
from pprint import pformat, pprint
import re
import subprocess
import sys
import time
from urllib.parse import unquote

import requests
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from .ext_packages import ExtPackage

from .py_packages import PyPackage
from .logger import ilog
from .backend_dirs import g_backend_dirs



g_backend_env = None

def generate_backend_env(exclude: list[str] | None = None) -> bool:
    global g_backend_env
    try:
        backend_env = _generate_backend_env(exclude=exclude)
        if backend_env is None:
            ilog.critical("Backend env generation returned None (unexpected).")
            return False

    except Exception as e:
        ilog.critical(f"Failed to define the backend environment: {str(e)}")
        return False

    g_backend_env = backend_env
    return True



def _generate_backend_env(exclude: list[str] | None = None) -> dict:
    # Environnment
    # ilog.info(f"Local environment:")
    # ilog.info(get_python_env())

    if exclude is None:
        forbidden_names: tuple[str] = (
            'python',
            'conda',
            'vapoursynth',
        )
    else:
        forbidden_names: tuple[str] = (
            'python',
            'conda',
            'vapoursynth',
        )

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

    # Set the Python-specific environment variables
    # not recommended, keep for the history
    # backend_env['PYTHONHOME'] = str(python_dir)
    # backend_env['PYTHONPATH'] = ":".join([
    #     str(g_backend_dirs.python_exe.parent),
    #     str(python_dir / 'lib' / 'python3.12'),
    #     str(python_dir / 'lib' / 'python3.12' / 'site-packages'),
    # ])

    # Set new PATH
    path_entries = original_path.split(sep)
    filtered_path_entries = []
    for entry in path_entries:
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
        [str(g_backend_dirs.python_exe.parent)] + filtered_path_entries
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




def get_python_version() -> str:
    # Run the python executable with the '-V' or '--version' flag to get the version
    version: str = ""
    try:
        result = subprocess.run(
            [str(g_backend_dirs.python_exe), '--version'],
            capture_output=True,
            text=True,
            env=g_backend_env
        )
        version = result.stdout.strip()
    except:
        pass
    return version



def update_pip() -> bool:
    python_exe = str(g_backend_dirs.python_exe)
    pip_command: str = f"{python_exe} -m pip install --upgrade pip"
    try:
        subprocess.run(
            pip_command.split(' '),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
            check=True,
            env=g_backend_env,
        )
    except subprocess.CalledProcessError as e:
        # Specific error if subprocess fails
        ilog.error(f"Error occurred while updating pip: {e}")
        return False
    except Exception as e:
        # Catch all other unexpected errors
        ilog.error(f"Unexpected error: {e}")
        return False
    return True



def update_package_info(package: PyPackage, retry: int = 3) -> None:
    installed_version: str = ""
    try:
        installed_version = metadata.metadata(package.name).json['version']
        ilog.debug(f"{package.pretty_name}: {installed_version}")
        package.installed_version = installed_version
    except:
        ilog.info(f"Package {package.pretty_name} is not installed")



def update_package_url(package: PyPackage, retry: int = 3) -> bool:
    timeout: float = 5
    _retry: int = retry
    if package.extra_index_url:
        regex: re.Pattern = re.compile(rf".*Downloading\s*(https:\/\/.*\/.*\.whl)")
    else:
        regex: re.Pattern = re.compile(rf".*{package.name}.*(https:\/\/.*\/.*\.whl)\.metadata")

    already_installed_regex = re.compile(rf".*Requirement\s*already\s*satisfied:\s*{package.name}")
    url: str = ""

    start_time: float = time.time()
    index_url: list[str] = ["--index-url", package.index_url] if package.index_url else []
    version = f"=={package.version}" if package.version != '' else ''
    pip_command: list[str] = [
        "python",
        "-m", "pip", "download",
        # "--no-deps",
        "--no-cache-dir",
        f"{package.name}{version}",
        *index_url,
        "--progress-bar=off",
        "-vvv"
    ]
    pip_command = list([x for x in pip_command if x != '' and x is not None])
    # print(' '.join(pip_command))
    while _retry > 0 and url == '' and not package.installed and package.supported:
        sub_process = subprocess.Popen(
            pip_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        start_time = time.time()
        while (
            (time.time() - start_time) < timeout + (retry - _retry) * 5
            and sub_process.poll() is None
        ):
            try:
                line = sub_process.stdout.readline().decode('utf-8').strip()
            except:
                break
            if package.name == 'torch':
                # and line.startswith("Obtaining dependency information"):
                print(lightcyan(line))

            # if _retry < retry:
            #     ilog.debug(line)

            if (result := re.search(regex, line)):
                sub_process.terminate()
                url = result.group(1)
                break

            if (result := re.search(already_installed_regex, line)):
                sub_process.terminate()
                package.installed = True
                break

            if "No matching distribution found" in line:
                sub_process.terminate()
                package.supported = False
                ilog.warning(f"[W] {package.pretty_name} is not supported on this platform")
                break

        if url == '' or package.installed:
            if sub_process.poll() is None:
                sub_process.terminate()
            while sub_process.poll() is None and (time.time() - start_time) > 2:
                time.sleep(0.5)

            if not package.installed and package.supported:
                _retry -= 1
                timeout += (retry - _retry) * 5
                ilog.warning(f"retry: {_retry}, new timeout: timeout")

    package.url = url
    if package.url == '' and not package.installed and package.supported:
        ilog.error(red(f"[E] Failed  to fetch url for {package.name}"))

    elif package.installed:
        ilog.info(f"{package.pretty_name} already installed")

    elif package.url != '':
        package.wheel = unquote(package.url.split('/')[-1])
        package.version = unquote(package.wheel.split('-')[1])
        response: requests.Response
        try:
            response = requests.get(package.url, stream=True)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            if str(e).startswith('404'):
                ilog.error(f"File {package.url} not found")
            return False
        package.size=int(response.headers.get('Content-length', 0))

    return True



def uninstall_py_package(package: PyPackage) -> bool:
    ilog.debug(f"uninstall {package.name}")
    pip_command: str = f"python -m pip uninstall -y {package.name}"
    try:
        subprocess.run(
            pip_command.split(' '),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except:
        return False
    return True



def install_py_packages(
    packages: tuple[PyPackage],
    retry: int = 3,
    threads: int = 1,
) -> bool:
    threads = min(max(threads, 1), len(packages))
    progress = Progress(
        TextColumn("[bold cyan]{task.fields[name]}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
    )

    def _get_info(package: PyPackage) -> None:
        update_package_info(package)
        update_package_url(package)
        ilog.debug(f"{package.pretty_name}: {package.url}")
        if package.supported:
            if not package.is_installed():
                ilog.info(orange(
                    f"{package.pretty_name} has to be updated: "
                    + f"{package.installed_version} -> {package.version}"
                ))
            else:
                ilog.info(lightgreen(
                    f"{package.pretty_name} is already installed: {package.version}"
                ))


    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(_get_info, packages)


    packages = [package for package in packages if not package.is_installed()]
    pprint(packages)
    if not packages:
        ilog.info(f"No packages to update")
        return True

    success: bool = True
    if threads == 1:
        with progress:
            for package in packages:
                success = download_install_py_package(
                    package,
                    progress=progress,
                    retry=retry
                )
                if not success:
                    break

    else:
        with progress:
            with ThreadPoolExecutor(max_workers=threads) as executor:
                for result in executor.map(
                    lambda args: download_install_py_package(*args),
                    [(package, progress, retry) for package in packages]
                ):
                    success = success and result

    if not success:
        return False

    # Install remaining packages
    print("remaining packages")
    for package in packages:
        if package.delayed_install and not package.installed:
            package.delayed_install = False
            download_install_py_package(package)

    return True



def download_install_py_package(
    package: PyPackage,
    progress: Progress| None = None,
    retry: int = 3
) -> bool:
    url: str = package.url
    temp_dir: Path = get_org_tempdir('herlegon')

    response: requests.Response
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        if str(e).startswith('404'):
            ilog.error(f"File {url} not found")
        return False

    # Use the external package download procedure
    ext_package = ExtPackage(
        name=package.pretty_name,
        filename=package.wheel,
        size=package.size,
        response=response,
        cache_file=temp_dir / "wheels" / package.wheel
    )

    # Download package
    if (
        ext_package.cache_file.is_file()
        and ext_package.cache_file.stat().st_size == ext_package.size
    ):
        ext_package.downloaded = True
        ilog.info(f"already downloaded")

    else:
        ext_package.downloaded = download_package_from_host(
            ext_package,
            progress=progress,
            task_id=progress.add_task(
                "[green] Installing...",
                name=ext_package.name,
                start=False
            ),
            retry=retry
        )

    pprint(ext_package)
    if not ext_package.downloaded:
        return False

    if not package.delayed_install:
        print("install non delayed")
        package.installed = install_py_package(package, ext_package)
        return package.installed
    return True

