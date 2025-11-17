from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
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
    install_dir.mkdir(parents=True, exist_ok=True)

    if extension == '.gz' and str(package.cache_file).endswith('.tar.gz'):
        import tarfile
        with tarfile.open(package.cache_file, "r:gz") as tar:
            tar.extractall(path=install_dir)

    elif extension == '.zip':
        import zipfile
        with zipfile.ZipFile(package.cache_file, "r") as zip_file:
            # Get all file paths in the zip
            all_files = zip_file.namelist()

            # Check if there's a single root folder
            root_folders = set()
            for file in all_files:
                parts = Path(file).parts
                if parts:
                    root_folders.add(parts[0])

            # If there's exactly one root folder and all files are under it
            has_single_root = len(root_folders) == 1
            if has_single_root:
                root_folder = root_folders.pop()
                # Extract each file, stripping the root folder from the path
                for file in all_files:
                    # Skip the root folder itself
                    if file == root_folder or file == root_folder + '/':
                        continue

                    # Remove root folder from path
                    new_path = Path(file).relative_to(root_folder)
                    target_path = install_dir / new_path

                    # Create directories if needed
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    # Write the file (skip if it's a directory)
                    if not file.endswith('/'):
                        source = zip_file.open(file)
                        target_path.write_bytes(source.read())
            else:
                # No single root folder, extract normally
                zip_file.extractall(install_dir)

    else:
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



