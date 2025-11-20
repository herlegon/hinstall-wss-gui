from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import os
from pathlib import Path
from pprint import pprint
import re
import signal
import subprocess
import sys
import time
import tomllib
from typing import Any

from hytils import lightcyan, lightgreen, red, yellow
from local_rehost import get_rehost_dir

sys.path.append(str(Path(__file__).resolve().parent.parent))
from hinstall import (
    parse_config_,
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

    packages_cfg = parse_config_(data)

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


    # Python packages
    keep_up_to_date: bool = False
    # g_backend_dirs.python_exe = "python"

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


    initial_packages = py_packages.get_initial()
    uninstalled_packages = initial_packages.get_not_installed()

    if True:
        cpu_count = multiprocessing.cpu_count()
        cpu_count = max(cpu_count - 1, int(cpu_count * 4 / 5))


        selected_pkgs = initial_packages
        start_time = time.time()
        if False:
            for pkg in selected_pkgs:
                pkg: PyPackage
                pkg.update_info()
        else:
            with ThreadPoolExecutor(max_workers=min(cpu_count, len(selected_pkgs))) as executor:
                executor.map(lambda pkg: pkg.update_info(), selected_pkgs)

        elapsed = time.time() - start_time
        for pkg in selected_pkgs:
            pkg: PyPackage
            print(f"{pkg.name}:\n    latest version: {pkg.latest_version}\n    selected: {pkg.version}")
            print(f"    variant: {pkg.variant}")
            print(f"    wheel: {pkg.wheel}")
            print(f"    wheel url: {pkg.wheel_url}")
            print(f"    size: {pkg.size // 1024}kB")
        ilog.info(f"updated in {elapsed:.02f}s")

        # sys.exit()


    python_exe = str(g_backend_dirs.python_exe)
    cache_dir = str(g_backend_dirs.cache)
    # Cache only the big packages
    print(f"Cache: {cache_dir}")
    print("Packages to install", lightcyan(", ".join((pkg.name for pkg in selected_pkgs))))

    for pkg in py_packages.get_delayed():
        pkg: PyPackage
        pkg.do_cache = True

        # if pkg.installed:
        #     continue
        # pprint(pkg)

        pnv = (
            "==".join((pkg.name, pkg.version))
            if pkg.version
            else pkg.name
        )
        # if pkg.name !=  "opencv-python":
        # if pkg.name !=  "torch" and "cu" not in pkg.version:
        #     continue

        if pkg.name != "tensorrt":
            continue

        if pkg.do_cache and pkg.name != "tensorrt":
            start_time = time.time()

            if True:
                cmd = f"{python_exe} -m pip download -d {cache_dir} --no-deps {pnv}"
                if pkg.extra_index_url:
                    cmd = f"{cmd} --index-url={pkg.extra_index_url}"
                print(yellow(cmd))
                try:
                    subprocess.run(cmd.split())
                except Exception as e:
                    ilog.critical(f"failed to download wheel: {str(e)}")

            elif False:
                print(red("download"))
                cmd = f"{python_exe} -m pip download -d {cache_dir} --no-deps {pnv}"
                # try:
                process = subprocess.Popen(
                    cmd.split(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                wheel = ""
                output_lines = []
                for line in process.stdout:
                    line = line.rstrip()
                    output_lines.append(line)

                    # Parse download progress (e.g., "Downloading torch-2.0.0-cp311-cp311-linux_x86_64.whl (2.3GB)")
                    if 'Downloading' in line:
                        # Extract size info if present
                        # Format: "Downloading package-1.0-py3-none-any.whl (1.2MB)"

                        if match := re.search(r'([^\s]+\.whl)(?!\.metadata)', line):
                            ilog.info(f"⬇️  {line}")
                            wheel = match.group(1)
                            break
                    #     else:
                    #         print(line)
                    else:
                        print(line)

                if not wheel:
                    print(output_lines)

                filepath = g_backend_dirs.cache / wheel
                print(red(filepath))

                # Monitor file growth
                while process.poll() is None:
                    if filepath.is_file():
                        current_size = filepath.stat().st_size
                        # Log progress based on file size
                        ilog.info(f"Downloaded: {current_size / (1024**2):.1f} MB")
                    time.sleep(0.2)



                    # for line in process.stdout:
                    #     line = line.rstrip()

                    #     # Parse download progress (e.g., "Downloading torch-2.0.0-cp311-cp311-linux_x86_64.whl (2.3GB)")
                    #     if 'Downloading' in line:
                    #         # Extract size info if present
                    #         # Format: "Downloading package-1.0-py3-none-any.whl (1.2MB)"
                    #         match = re.search(r'([\d.]+\s*[KMGT]B)', line)
                    #         if match:
                    #             ilog.info(f"⬇️  {line}")
                    #         else:
                    #             ilog.info(f"⬇️  {line}")

                    #     else:
                    #         print(lightcyan(line))
                    # process.wait()
                    # if process.returncode != 0:
                    #     ilog.error(f"Download failed with code {process.returncode}")

                # except Exception as e:
                #     ilog.critical(f"failed to download wheel: {str(e)}")

                print(red("END "))

            else:
                # torch-2.9.1+cu130-cp312-cp312-win_amd64.whl
                #   24s

                # pkg.update_info()
                wheel_fp: Path = g_backend_dirs.cache / pkg.wheel
                if wheel_fp.is_file():
                    print(lightgreen(f"Already downloaded {wheel_fp}"))
                else:
                    print(red(f"error: wheel file {wheel_fp} shall exist before"))

                # pkg.download_wheel()

            elapsed = time.time() - start_time
            ilog.info(f"{pkg.name} downloaded in {elapsed:.02f}s")
            # break

        if pkg.name == "tensorrt":
            cmd = f"{python_exe} -m pip install --find-links {cache_dir} {pnv}"
            pprint(os.environ)
            print(yellow(cmd))
            pprint(backend_env)
            backend_env = generate_backend_env()
            try:
                subprocess.run(
                    cmd.split(),
                    env=backend_env,
                )
            except Exception as e:
                ilog.critical(f"failed to install package {pkg.name}: {str(e)}")


    # for pkg in initial_packages:
    #     pkg.uninstall()
