from concurrent.futures import ThreadPoolExecutor
from pprint import pprint
from hytils import (
    get_extension,
    red,
)
from pathlib import Path
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
import shutil
import tempfile

from .backend_dirs import g_backend_dirs
from .ext_package import ExtPackage
from .logger import ilog
from .utils import (
    extract_tar_file,
    extract_zip_file,
)



def download_package_(
    package: ExtPackage,
    progress: Progress | None = None,
    reinstall: bool = False,
) -> ExtPackage:

    if package.is_up_to_date() and not reinstall:
        package.clean_cache()
        return package

    if package.is_installed() and not reinstall:
        if not package.do_cache:
            try:
                package.cache_file.unlink()
            except:
                pass
        package.clean_cache()
        return package

    # Dowanload an install
    package.installed = False

    is_cached = package.is_cached()

    # Use local host to simulate a download
    if (
        not is_cached
        and package.use_local_host
        and g_backend_dirs.local_host
    ):
        package.download_from_local_host()

    # Finally download it from host
    if not package.downloaded and package.downloadable:
        package.download_package_from_host(
            progress=progress,
            task_id=progress.add_task(
                "[green] Installing...",
                name=package.name,
                start=False
            ),
        )

    return package



def dl_and_install_ext_package(
    package: ExtPackage,
    progress: Progress | None = None,
    reinstall: bool = False,
) -> bool:
    if package.skip:
        return True
    ilog.info(f"{package.name}")

    package = download_package_(
        package,
        progress=progress,
        reinstall=reinstall,
    )

    # Install package
    if not package.installed or reinstall:
        package.install(progress=progress)

    if package.installed:
        ilog.info(f"{package.name}: installed")
    else:
        ilog.error(f"{package.name}: failed to install")

    return package.installed



def download_install_ext_packages(
    packages: list[ExtPackage] | ExtPackage,
    retry: int = 3,
    threads: int = 1,
    reinstall: bool = False,
    use_local_host: bool = False,
) -> bool:
    if isinstance(packages, list):
        packages = [package for package in packages if not package.skip]
    else:
        packages = (
            [packages]
            if not packages.skip
            else []
        )

    ilog.info(f"use local host: {use_local_host}")
    for pkg in packages:
        pkg.use_local_host = use_local_host
        pkg.retry_count = retry


    threads = min(max(threads, 1), len(packages))
    progress = Progress(
        TextColumn("[bold cyan]{task.fields[name]}", justify="right"),
        BarColumn(bar_width=40),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
    )

    if threads == 1:
        with progress:
            for package in packages:
                success = dl_and_install_ext_package(
                    package=package,
                    progress=progress,
                    reinstall=reinstall,
                )
                if not success:
                    return False
    else:
        success: bool = True
        with progress:
            with ThreadPoolExecutor(max_workers=threads) as executor:
                for result in executor.map(
                    lambda args: dl_and_install_ext_package(**args),
                    [
                        {
                            'package': package,
                            'progress': progress,
                            'reinstall': reinstall
                        }
                        for package in packages
                    ]
                ):
                    success = success and result
        return success

    return True



