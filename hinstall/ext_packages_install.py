from concurrent.futures import ThreadPoolExecutor
import shutil
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from hytils import (
    get_extension,
    red,
)
from .ext_packages import ExtPackage
from .ext_packages_dl import (
    clean_cache,
    download_package_,
)
from .logger import ilog



def install_ext_package(package: ExtPackage) -> bool:
    install_dir = package.install_dir
    ilog.debug(f"Install: {package.name} in {install_dir}")

    extension: str = get_extension(str(package.cache_file))
    if install_dir.exists():
        shutil.rmtree(install_dir)

    if extension == '.gz' and str(package.cache_file).endswith('.tar.gz'):
        import tarfile
        install_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(package.cache_file, "r:gz") as tar:
            tar.extractall(path=install_dir)

    elif extension == '.zip':
        import zipfile
        with zipfile.ZipFile(package.cache_file, "r") as f:
            f.extractall(install_dir)

    else:
        install_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(package.cache_file, install_dir)

    (install_dir / package.tag).touch()
    package.installed = True

    ilog.debug(f"{package.name} installed in {install_dir}")

    return True



def dl_and_install_ext_package(
    package: ExtPackage,
    progress: Progress | None = None,
    retry: int = 3,
    use_local_host: bool = False,
    reinstall: bool = False,
) -> bool:
    if package.skip:
        return True
    ilog.info(f"{package.name}")
    package = download_package_(
        package,
        progress=progress,
        retry=retry,
        use_local_host=use_local_host,
        reinstall=reinstall,
    )

    # Install package
    if not package.installed or reinstall:
        if package.downloaded:
            installed: bool = install_ext_package(package)
            if installed:
                clean_cache(package=package)
            package.installed = installed

    if package.installed:
        ilog.info(f"{package.name}: installed")
    else:
        ilog.error(f"{package.name}: failed to install")

    return package.installed



def download_install_ext_packages(
    packages: list[ExtPackage],
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
                    retry=retry,
                    use_local_host=use_local_host,
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
                            'retry': retry,
                            'use_local_host': use_local_host,
                            'reinstall': reinstall
                        }
                        for package in packages
                    ]
                ):
                    success = success and result
        return success

    return True



