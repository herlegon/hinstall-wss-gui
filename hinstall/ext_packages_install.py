from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pprint import pprint
import shutil
from tarfile import TarFile
import time
from zipfile import ZipFile
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

def extract_zip_file(
    compressed_data: ZipFile,
    install_dir: Path,
    exclude: list[str] = [],
    progress: Progress | None = None,
    task_id = None
) -> None:
    """Extract ZIP archive with progress tracking, excluding specified names"""

    def should_exclude(path: Path) -> bool:
        """Check if any part of the path matches excluded names"""
        return any(part in exclude for part in path.parts) or path.name in exclude

    all_files = compressed_data.namelist()

    # Check for single root folder
    root_folders = set()
    for file in all_files:
        parts = Path(file).parts
        if parts:
            root_folders.add(parts[0])

    has_single_root = len(root_folders) == 1
    root_folder = root_folders.pop() if has_single_root else None

    # Calculate total size
    total_bytes = sum(
        compressed_data.getinfo(f).file_size
        for f in all_files
        if not f.endswith('/')
    )

    if progress is not None and task_id is not None:
        progress.update(task_id, total=total_bytes)

    # Extract files
    for file in all_files:
        if file.endswith('/'):
            continue

        file_path = Path(file)

        # Handle single root folder
        if has_single_root and root_folder is not None:
            if file == root_folder or file == f'{root_folder}/':
                continue
            file_path = file_path.relative_to(root_folder)

        file_size = compressed_data.getinfo(file).file_size

        if should_exclude(file_path):
            if progress is not None and task_id is not None:
                progress.update(task_id, advance=file_size)
            continue

        target_path = install_dir / file_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with compressed_data.open(file) as source:
            target_path.write_bytes(source.read())

        if progress is not None and task_id is not None:
            progress.update(task_id, advance=file_size)


def extract_tar_file(
    compressed_data: TarFile,
    install_dir: Path,
    exclude: list[str] = [],
    progress: Progress | None = None,
    task_id = None
) -> None:
    """Extract TAR archive with progress tracking, excluding specified names"""

    def should_exclude(path: Path) -> bool:
        """Check if any part of the path matches excluded names"""
        return any(part in exclude for part in path.parts) or path.name in exclude

    # start_time = time.time()
    # Single pass: collect members, detect root, calculate size
    all_members = []
    root_folders = set()
    total_bytes = 0

    for member in compressed_data:  # Iterator - same as getmembers() but cleaner
        all_members.append(member)

        if member.isfile():
            total_bytes += member.size

        parts = Path(member.name).parts
        if parts:
            root_folders.add(parts[0])

    has_single_root = len(root_folders) == 1
    root_folder = root_folders.pop() if has_single_root else None

    if progress is not None and task_id is not None:
        progress.update(task_id, total=total_bytes)
    # print(f"elapsed: {time.time() - start_time:.1f}")

    # Extract files
    for member in all_members:
        if not member.isfile():
            continue

        file_path = Path(member.name)

        # Handle single root folder
        if has_single_root and root_folder is not None:
            if member.name == root_folder or member.name == f'{root_folder}/':
                continue
            file_path = file_path.relative_to(root_folder)

        if should_exclude(file_path):
            if progress is not None and task_id is not None:
                progress.update(task_id, advance=member.size)
            continue

        target_path = install_dir / file_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        source = compressed_data.extractfile(member)
        if source:
            target_path.write_bytes(source.read())

        if progress is not None and task_id is not None:
            progress.update(task_id, advance=member.size)



def install_ext_package(
    package: ExtPackage,
    progress: Progress | None = None,
) -> bool:
    install_dir = package.install_dir
    ilog.debug(f"Install: {package.name} in {install_dir}")
    print(progress)

    extension: str = get_extension(str(package.cache_file))
    if install_dir.exists():
        shutil.rmtree(install_dir)
    install_dir.mkdir(parents=True, exist_ok=True)

    exclude: list[str] = []
    if package.key.lower() == 'ffmpeg':
        exclude = ('doc', 'man', 'ffplay')

    if (
        extension in ('.gz', '.xz')
        and str(package.cache_file).endswith(f'.tar{extension}')
    ):
        task_id=progress.add_task(
            "[green] Extracting...", name=package.name, start=True
        )
        print(red(f'.tar{extension}'))
        import tarfile
        compression = extension.lstrip('.')
        with tarfile.open(package.cache_file, f"r:{compression}") as tar_file:
            extract_tar_file(
                tar_file,
                install_dir=install_dir,
                exclude=exclude,
                progress=progress,
                task_id=task_id,
            )

    elif extension == '.zip':
        import zipfile
        with zipfile.ZipFile(package.cache_file, "r") as zip_file:
            task_id=progress.add_task(
                "[green] Extracting...", name=package.name, start=True
            )
            extract_zip_file(
                zip_file,
                install_dir=install_dir,
                exclude=exclude,
                progress=progress,
                task_id=task_id,
            )

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
            installed: bool = install_ext_package(package, progress=progress)
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



