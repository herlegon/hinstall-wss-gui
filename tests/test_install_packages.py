from pathlib import Path
from pprint import pprint
import signal
import sys
import tomllib
from typing import Any

from hytils import lightcyan, lightgreen, red
sys.path.append(str(Path(__file__).resolve().parent.parent))

from hinstall import (
    ilog,
    parse_packages_toml_,
    ExtPackages,
    g_backend_dirs,
    get_rehost_dir,
    download_install_ext_packages,
)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    with open(Path("packages.toml"), "rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    packages_cfg = parse_packages_toml_(data)
    pprint(packages_cfg)

    external_packages = ExtPackages(packages_cfg, sys.platform)
    external_packages.get_all_except('python')
    print(lightcyan(" ".join (("-" * 40, sys.platform, "-" * 40))))
    pprint(external_packages)
    print()

    python_package = external_packages.get_by_key('python')
    print(lightcyan(" ".join (("-" * 40, "python", "-" * 40))))
    pprint(python_package)
    print()

    g_backend_dirs.local_host = get_rehost_dir()
    print(lightcyan(" ".join (("-" * 40, "backend directories", "-" * 40))))
    pprint(g_backend_dirs)


    if python_package:
        installed: bool = download_install_ext_packages(
            packages=python_package,
            reinstall=True,
            threads=1,
            use_local_host=True
        )
        if installed:
            print(lightgreen("All packages installed"))
        else:
            print(red("Error: missing package(s)"))
    else:
        print(lightgreen("No packages to install"))


    if external_packages:
        installed: bool = download_install_ext_packages(
            packages=external_packages,
            reinstall=True,
            threads=1,
            use_local_host=True
        )
        if installed:
            print(lightgreen("All packages installed"))
        else:
            print(red("Error: missing package(s)"))
    else:
        print(lightgreen("No packages to install"))

