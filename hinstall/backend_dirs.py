from dataclasses import dataclass
import sys
import os
from pathlib import Path



@dataclass(slots=True)
class BackendDirectories:
    app: Path
    python_exe: Path
    external: Path
    cache: Path
    models: Path
    local_host: Path | None = None



def get_backend_dirs(
    app_name: str = "herlecon_convert",
    company: str = "herlegon"
) -> BackendDirectories:
    """Get platform-specific backend directory"""

    if sys.platform == "win32":
        # Windows: Use AppData\Local
        base = Path(
            os.environ.get('LOCALAPPDATA', Path.home() / "AppData" / "Local")
        )
        cache_dir = base / company / "cache"
        python_exe = "python.exe"

    elif sys.platform == "linux":
        # Linux: Use XDG Base Directory
        base = Path(os.environ.get('XDG_DATA_HOME', Path.home() / ".local" / "share"))
        cache_dir = Path(os.environ.get('XDG_DATA_HOME', Path.home() / company / "cache"))
        python_exe = "python"

    elif sys.platform == "darwin":
        # macOS: Use Application Support
        base = Path.home() / "Library" / "Application Support"
        cache_dir = base / company / "cache"
        python_exe = "python"

    else:
        ilog.error(f"Unsupported platform: {sys.platform}")

    return BackendDirectories(
        app=base / company / app_name,
        python_exe=base / company / app_name / "python" / python_exe,
        external=base / company / app_name,
        cache=cache_dir,
        models=base / company / "models",
    )
g_backend_dirs: BackendDirectories = get_backend_dirs()



def get_rehost_dir(company: str = "herlegon") -> Path:
    local_package_dir: Path

    if sys.platform == "win32":
        local_package_dir = Path("A:\\") / company / "rehost"

    elif sys.platform == "linux":
        local_package_dir = Path("/opt") / company / "rehost"

    elif sys.platform == "darwin":
        local_package_dir = Path.home() / company / "rehost"

    return local_package_dir

