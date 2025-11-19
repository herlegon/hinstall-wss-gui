from pathlib import Path
from pprint import pprint
import signal
import sys
import tomllib
from typing import Any

from hytils import lightcyan, lightgreen, red
from local_rehost import get_rehost_dir

sys.path.append(str(Path(__file__).resolve().parent.parent))
from hinstall import (
    parse_packages_toml_,
    ExtPackages,
    PyPackages,
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


    py_packages = PyPackages(packages_cfg, sys.platform)
    py_packages = py_packages.get_initial()
    pprint(py_packages)

    print(get_python_version())


    get_pypackage_list()

    # update_package_info(py_packages[0])

    installed_versions = get_pip_versions()
    pprint(installed_versions)

    # install_py_packages(
    #     python_exe=python_exe,
    #     packages=py_packages(),
    #     threads=4
    # )
