from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from pathlib import Path
from pprint import pprint
import signal
import subprocess
import sys
import time
import tomllib
from typing import Any

from hytils import lightcyan, lightgreen, red
from local_rehost import get_rehost_dir

sys.path.append(str(Path(__file__).resolve().parent.parent))
from hinstall import (
    parse_packages_toml_,
    ExtPackages,
    PyPackages,
    PyPackage,
    g_backend_dirs,
    download_install_ext_packages,
    generate_backend_env,
    get_python_version,
    ilog,
    get_pip_versions,
    get_pypackage_list,
)



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    tool = "hconvert"

    config_fp = (Path(__file__).parent / "configs" / f"{tool}.toml").resolve()
    print(f"loading config: {config_fp}")
    with open(config_fp, "rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    packages_cfg = parse_packages_toml_(data)

    # Install python if not yest installed
    python_package = ExtPackages(packages_cfg, sys.platform).get_by_key('python')
    pprint(python_package)

    # Use local rehost
    g_backend_dirs.local_host = get_rehost_dir()
    python_package.use_local_host = True

    if not python_package.is_installed():
        ilog.error(f"{python_package.name} is not installed. Installing...")
        installed: bool = download_install_ext_packages(
            packages=python_package,
            reinstall=False,
            use_local_host=True
        )
        if not python_package.installed:
            ilog.error(f"Error: {python_package.name} not installed")
            sys.exit(-1)
    else:
        ilog.info(f"{python_package.name} is installed.")

    backend_env = generate_backend_env()


    keep_up_to_date: bool = False

    py_packages = PyPackages(
        packages_cfg,
        sys.platform,
        keep_up_to_date=keep_up_to_date
    )

    # Display the package sthat have to be installed first
    if False:
        py_packages = py_packages.get_initial()

    # Python version
    print(get_python_version())

    # List uninstalled python packages
    if False:
        uninstalled_packages = py_packages.get_not_installed()
        print("uninstalled")
        pprint(uninstalled_packages)

    # get_pypackage_list()
    # update_package_info(py_packages[0])

    # For testing purpose: get the current installed versions
    if False:
        installed_versions = get_pip_versions()


    # Update wheels
    if False:
        uninstalled_packages = py_packages.get_delayed().get_not_installed()
        pprint(f"get wheel url")
        for pkg in uninstalled_packages:
            pkg: PyPackage
            pkg.update_wheel_url()
        pprint(uninstalled_packages)

    if False:
        # uninstalled_packages = py_packages.get_initial().get_not_installed()
        uninstalled_packages = py_packages.get_not_installed()
        for pkg in uninstalled_packages:
            pkg: PyPackage
            if (
                pkg.variant in 'cuda'
                or pkg.name == 'tensorrt'
                or not pkg.delayed_install
            ):
                pkg.fetch_latest_version()
                print(f"{pkg.name}:\n    latest version: {pkg.latest_version}\n    selected: {pkg.version}")
                print(f"    variant: {pkg.variant}")
                start_time = time.time()
                pkg.update_info()
                print(f"    wheel: {pkg.wheel}")
                print(f"    size: {pkg.size}")


    python_exe = str(g_backend_dirs.python_exe)
    cache_dir = str(g_backend_dirs.cache)
    # Cache only the big packages
    if False:
        print(f"use cache: {cache_dir}")
        subprocess.run([
            python_exe,
            '-m', 'pip', 'download',
            '-d', cache_dir,
            '--no-deps',
            'psutil'
        ])

    # Install package
    if False:
        subprocess.run([
            python_exe,
            '-m', 'pip', 'install',
            '--find-links', cache_dir,
            'psutil'
        ])


    if True:
        cpu_count = multiprocessing.cpu_count()
        cpu_count = max(cpu_count - 1, int(cpu_count * 4 / 5))


        # uninstalled_packages = py_packages.get_initial().get_not_installed()
        uninstalled_packages = py_packages.get_initial().get_not_installed()
        start_time = time.time()
        if False:
            for pkg in uninstalled_packages:
                pkg: PyPackage
                pkg.update_info()
        else:
            with ThreadPoolExecutor(max_workers=min(cpu_count, len(uninstalled_packages))) as executor:
                executor.map(lambda pkg: pkg.update_info(), uninstalled_packages)

        elapsed = time.time() - start_time
        for pkg in uninstalled_packages:
            pkg: PyPackage
            print(f"{pkg.name}:\n    latest version: {pkg.latest_version}\n    selected: {pkg.version}")
            print(f"    variant: {pkg.variant}")
            print(f"    wheel: {pkg.wheel}")
            print(f"    wheel url: {pkg.wheel_url}")
            print(f"    size: {pkg.size:.01f}MB")
        ilog.info(f"updated in {elapsed:.02f}s")




