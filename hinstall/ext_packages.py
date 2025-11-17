
from dataclasses import dataclass
from pathlib import Path
import requests
import sys
from typing import Any
from .backend_dirs import g_backend_dirs
from .logger import ilog


PACKAGES: tuple[str] = (
    'ffmpeg',
    'vspython',
    'avs',
)


@dataclass
class ExtPackage:
    name: str
    filename: str
    key: str

    # Installation, skip is not necessary except for dev and to keep the
    # definitions in the config file
    skip: bool
    install_dir: Path = None
    installed: bool = False

    # Where to download from
    tag: Path = None
    size: int = 0
    host: str = ''
    response: requests.Response | None = None

    # Downloaded/cached
    downloaded: bool = False
    cache_file: Path = None
    do_cache: bool = False

    def __post_init__(self):
        self.skip = bool(self.filename == '')



class ExtPackages(list):

    def __init__(
        self,
        config: dict = None,
        platform: str = ""
    ):
        super().__init__()
        if config:
            if not platform:
                platform = sys.platform
            self._parse_and_populate(config, platform)


    def _parse_and_populate(self, config: dict, platform: str):

        install_dir: Path = g_backend_dirs.external

        # Automatically select the current platform if not specified
        #  used for validation
        if platform is None:
            platform = sys.platform

        # Get the platform-specific config
        platform_config: dict[str, Any] = (
            config['packages'].get(platform, {})
        )
        default_config: dict[str, Any] = platform_config.get('default', {})
        pretty_names: dict[str, str] = default_config.get('names', {})

        for key, value in platform_config.items():
            # Skip if it's a simple value or the default section
            if not isinstance(value, dict) or key == 'default':
                continue

            # Check if this looks like a package definition (has filename or is explicitly configured)
            if 'filename' in value:
                skip = value.get('skip', False)
                ilog.debug(f"{key}: skip={skip}")
                if not skip:
                    self.append(
                        ExtPackage(
                            name=pretty_names.get(key, key),
                            filename=value.get('filename', ''),
                            key=key,
                            install_dir=install_dir / key,
                            host=value.get('host', ''),
                            do_cache=value.get('do_cache', False),
                            skip=value.get('skip', False),
                        )
                    )

        for p in self:
            for k in ('host', 'do_cache'):
                # keys are accessibles because it's a dataclass with slots=False
                if k in p.__dict__ and not p.__dict__[k]:
                    instance = p.__dict__[k]
                    p.__dict__[k] = default_config.get(
                        k,
                        False if isinstance(instance, bool)
                        else "" if isinstance(instance, str)
                        else None
                    )


    def get_by_key(self, key: str) -> ExtPackage | None:
        for pkg in self:
            if pkg.key == key:
                return pkg
        return None


    def get_all_except(self, key: str) -> 'ExtPackages':
        result = ExtPackages()
        result.extend([pkg for pkg in self if pkg.key != key])
        return result


    def get_installed(self) -> 'ExtPackages':
        result = ExtPackages()
        result.extend([pkg for pkg in self if pkg.installed])
        return result


    def get_not_installed(self) -> 'ExtPackages':
        result = ExtPackages()
        result.extend([pkg for pkg in self if not pkg.installed])
        return result
