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
    g_backend_dirs,
    download_install_ext_packages,
)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    tool = "hconvert"

    config_fp = (Path(__file__).parent / "configs" / f"{tool}.toml").resolve()
    print(f"loading config: {config_fp}")
    with open(config_fp, "rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    packages_cfg = parse_packages_toml_(data)
    pprint(packages_cfg)

    external_packages = ExtPackages(packages_cfg, sys.platform)

    # All except python
    packages_to_install = external_packages.get_all_except('python')
    print(lightcyan(" ".join (("-" * 40, sys.platform, "-" * 40))))
    pprint(packages_to_install)
    print()

    g_backend_dirs.local_host = get_rehost_dir()
    print(lightcyan(" ".join (("-" * 40, "backend directories", "-" * 40))))
    pprint(g_backend_dirs)

    if packages_to_install:
        installed: bool = download_install_ext_packages(
            packages=packages_to_install,
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

