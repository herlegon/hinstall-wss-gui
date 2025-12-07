import os
from pathlib import Path
from pprint import pprint
import sys
import tomllib
from typing import Any
from warnings import warn

from hytils import yellow



class UserSettings:
    """Specific to installations of Herlegon products
    """

    def __init__(self) -> None:

        self.settings_dir: Path = self._platform_config_dir().joinpath("herlegon")
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        self.settings_fp: Path = self.settings_dir.joinpath("herlegon.toml")

        self.section: str = 'install'

        # Initialize default preferences
        self._settings: dict[str, list | str | int | float | bool | dict] = {
            'cache': True,
            'install_dir': "",
            'custom_install_dir': False,
            'ffmpeg_selection': 'lgpl', # lgpl, gpl, user (from FfmpegSelection)
            'ffmpeg_user_dir': "",
        }

        if not self.settings_fp.exists():
            return

        try:
            with self.settings_fp.open("rb") as f:
                data = tomllib.load(f)
                if self.section in data.keys():
                    self._settings.update(data[self.section])

        except Exception as e:
            warn(f"Warning: could not read {self.settings_fp}: {e}")


    @property
    def settings(self) -> dict[str, Any]:
        return self._settings


    def _platform_config_dir(self) -> Path:
        """
        - Windows: %APPDATA%/{org_name}/{app_name}/settings.toml
        - macOS: ~/Library/Application Support/{org_name}/{app_name}/settings.toml
        - Linux: ~/.config/{org_name}/{app_name}/settings.toml
        """
        home = Path.home()
        if sys.platform == "win32":
            base = Path(os.getenv("APPDATA", home.joinpath("AppData", "Roaming")))
        elif sys.platform == "darwin":
            base = home.joinpath("Library", "Application Support")
        else:
            base = Path(os.getenv("XDG_CONFIG_HOME", home.joinpath(".config")))
        return base


    def update(self, settings: dict[str, list | str | int | float | bool | dict] | None = None) -> None:
        if settings is None:
            return

        do_save: bool = False
        for k, v in self.settings.items():
            if k in settings.keys():
                if settings[k] != v:
                    do_save = True
                self.settings[k] = settings[k]

        if not do_save:
            return

        lines: list[str] = [f"[{self.section}]"]
        for key, value in self.settings.items():

            if isinstance(value, Path):
                # Convert paths to posix and quote strings
                lines.append(f"{key} = {value.as_posix()}")

            elif isinstance(value, str):
                if not value:
                    continue
                # Detect potential paths with backslash or colon
                lines.append(f'{key} = "{value.replace("\\", "/")}"')

            elif isinstance(value, bool):
                lines.append(f"{key} = {'true' if value else 'false'}")

            elif isinstance(value, (int, float)):
                lines.append(f'{key} = "{value}"')

            else:
                lines.append(f'{key} = "{value}"')

        try:
            self.settings_fp.write_text("\n".join(lines), encoding="utf-8")
        except Exception as e:
            print(f"Warning: could not write {self.settings_fp}: {e}")

