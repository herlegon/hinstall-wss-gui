from copy import deepcopy
from ext_packages import ExtPackages
from hytils import lightcyan, lightgreen
from pathlib import Path
from pprint import pprint
from py_packages import PyPackages
import sys
import tomllib
from typing import Any
from utils import PLATFORMS



def parse_packages_toml_(data: dict[str, Any]) -> dict[str, Any]:
    """
    Load TOML [platforms], capturing all keys as defaults and merging platform-specific packages.
    """
    for k_section in data.keys():
        section: dict[str, Any] = data[k_section]

        # Separate default configs from platform-specific configs
        default_config = {}
        platform_config = {}
        to_remove = []
        for key, value in section.items():
            if key in PLATFORMS:
                platform_config[key] = value
            else:
                default_config[key] = value
                to_remove.append(key)
        for k in to_remove:
            del section[k]

        # Merge defaults with each platform-specific config
        for platform in PLATFORMS:
            # Create a new section for undefined platform
            if platform not in platform_config.keys():
                platform_config[platform] = {}

            # Merge default keys
            platform_default = deepcopy(default_config)
            to_remove = []
            for k, v in platform_config[platform].items():
                if not isinstance(v, dict):
                    platform_default.update({k: v})
                    to_remove.append(k)
            for k in to_remove:
                del platform_config[platform][k]

            # Append the consolidated default section
            platform_config[platform]['default'] = platform_default

        data[k_section] = platform_config

    return data




if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    with open(Path("packages.toml"), "rb") as f:
        data: dict[str, Any] = tomllib.load(f)

    # load package toml cfg
    packages_cfg = parse_packages_toml_(data)

    print(lightgreen(" ".join(("-" * 40, "config", "-" * 40))))
    pprint(packages_cfg)


    if False:
        for platform_key in PLATFORMS:
            print(lightcyan(" ".join (("-" * 40, platform_key, "-" * 40))))
            packages = ExtPackages(packages_cfg, platform=platform_key)
            pprint(packages)
            print()

    if True:
        print(lightcyan(" ".join (("-" * 40, sys.platform, "-" * 40))))
        packages = ExtPackages(packages_cfg)
        pprint(packages)
        print()


    else:
        platform_key = sys.platform
        print(lightcyan(" ".join (("-" * 40, platform_key, "-" * 40))))
        packages = PyPackages(
            packages_cfg,
            # install_dir=g_backend_dirs.python_exe.parent,
            platform=platform_key,
            # section='py_packages',
        )
        print(lightcyan(" ".join (("-" * 40, "initial", "-" * 40))))
        pprint(packages.get_initial())
        print(lightcyan(" ".join (("-" * 40, "delayed", "-" * 40))))
        pprint(packages.get_delayed())
        pprint(packages.get_pypi_variant_names())
        print(lightcyan(" ".join (("-" * 40, "delayed", "-" * 40))))
        pprint(packages.get_by_variant("cuda"))
        print()
