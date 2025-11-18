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
    get_backend_env,
    g_backend_env,
    get_python_version,
    ilog,
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
    if not python_package.is_installed():
        ilog.error("Python is not installed")
        installed: bool = download_install_ext_packages(
            packages=python_package,
            reinstall=False,
            threads=1,
            use_local_host=True
        )
        if not python_package.installed:
            ilog.error("Error: python not installed")
            sys.exit(-1)


    py_packages = PyPackages(packages_cfg, sys.platform)
    py_packages = py_packages.get_initial()
    pprint(py_packages)



    if python_package:
        installed: bool = download_install_ext_packages(
            packages=python_package,
            reinstall=False,
            threads=1,
            use_local_host=True
        )
        if installed:
            print(lightgreen("Python package installed"))
        else:
            print(red("Error: python not installed"))
    else:
        print(red("Error: no package to install"))



    # Use backend python
    print(get_python_version())

    # get_standalone_env()
    # success: bool = update_pip(python_exe)
    # if success:
    #     logger.info("[I] pip is up-to-date")
    # else:
    #     logger.warning("[W] Failed updating pip")

    # install_py_packages(
    #     python_exe=python_exe,
    #     packages=py_packages(),
    #     threads=4
    # )
