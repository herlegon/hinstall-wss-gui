import os
from pathlib import Path
from pprint import pprint
from tarfile import TarFile, TarInfo
from zipfile import ZipFile
from rich.progress import (
    Progress,
)
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse

from hytils import red
from .logger import ilog



PLATFORMS: tuple[str] = ('win32', 'linux', 'darwin')


def get_domain_from_url(url: str) -> str:
    parsed_url = urlparse(url)
    # Extract the netloc (domain) part and remove the "www." prefix if present
    domain = parsed_url.netloc
    if domain.startswith("www."):
        domain = domain[4:]  # Remove the "www." prefix
    return domain



def check_site_reachable(url: str, max_retries: int = 3):
    """Check if site is reachable with retries"""
    for attempt in range(max_retries):
        try:
            # Ensure the URL includes the scheme (https://)
            if not url.startswith('http'):
                url = 'https://' + url

            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            urlopen(req, timeout=1)
            return True

        except (URLError, HTTPError) as e:
            ilog.debug(f"{url} is not reachable, retry {attempt} - {e}")
            if attempt < max_retries - 1:
                continue
    return False



class ProgressWrapper:
    def __init__(self, raw_response, progress: Progress, task_id, update_threshold=512*1024):
        self.raw = raw_response
        self.progress = progress
        self.task_id = task_id
        self.update_threshold = update_threshold
        self.bytes_downloaded = 0

    def read(self, size=-1):
        data = self.raw.read(size)
        if data and self.progress is not None:
            self.bytes_downloaded += len(data)
            if self.bytes_downloaded >= self.update_threshold:
                self.progress.update(self.task_id, advance=self.bytes_downloaded)
                self.bytes_downloaded = 0
        return data

    def flush_progress(self):
        """Call this after download completes to update remaining bytes"""
        if self.progress is not None and self.bytes_downloaded > 0:
            self.progress.update(self.task_id, advance=self.bytes_downloaded)
            self.bytes_downloaded = 0



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
    exclude: list[str] = None,
    progress: Progress | None = None,
    task_id=None
) -> None:
    if True:
        _extract_tar_file_file_count(
            compressed_data,
            install_dir,
            exclude,
            progress,
            task_id,
        )
    else:
        _extract_tar_file_file_size(
            compressed_data,
            install_dir,
            exclude,
            progress,
            task_id,
        )



def _extract_tar_file_file_size(
    compressed_data: TarFile,
    install_dir: Path,
    exclude: list[str] = None,
    progress: Progress | None = None,
    task_id=None
) -> None:
    """Extract TAR archive with progress tracking (based on file sizes),
       excluding specified names, without double extraction.
    """

    if exclude is None:
        exclude = []

    def should_exclude(path: Path) -> bool:
        """Check if any part of the path matches excluded names"""
        return any(part in exclude for part in path.parts) or path.name in exclude

    # ---------- FAST PRE-SCAN (NO EXTRACTION) ----------
    members = compressed_data.getmembers()

    # Count only files for size (symlinks have no data)
    total_bytes = sum(m.size for m in members if m.isfile())

    # Detect single root folder
    root_folders = {Path(m.name).parts[0] for m in members if Path(m.name).parts}
    has_single_root = len(root_folders) == 1
    root_folder = next(iter(root_folders)) if has_single_root else None

    show_progress: bool = progress and task_id is not None
    if show_progress:
        progress.update(task_id, total=total_bytes)

    # ---------- EXTRACTION ----------
    extracted_bytes = 0

    for member in members:
        file_path = Path(member.name)

        # strip root folder
        if has_single_root and root_folder:
            if file_path.parts and file_path.parts[0] == root_folder:
                file_path = file_path.relative_to(root_folder)

        # Skip excluded paths
        if should_exclude(file_path):
            if show_progress and member.isfile():
                progress.update(task_id, advance=member.size)
            continue

        target_path = install_dir / file_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Regular file
        if member.isfile():
            source = compressed_data.extractfile(member)
            if source:
                target_path.write_bytes(source.read())
            os.chmod(target_path, member.mode)

        # Symbolic link
        elif member.issym():
            if target_path.exists() or target_path.is_symlink():
                target_path.unlink()
            target_path.symlink_to(member.linkname)

        # Hard link
        elif member.islnk():
            link_target = Path(member.linkname)
            if has_single_root and root_folder and link_target.parts[0] == root_folder:
                link_target = link_target.relative_to(root_folder)
            target_path.hardlink_to(install_dir / link_target)

        # Progress update (only for actual file data)
        if show_progress and member.isfile():
            extracted_bytes += member.size
            progress.update(task_id, advance=member.size)




def _extract_tar_file_file_count(
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

    members = compressed_data.getmembers()
    file_members = [m for m in members
                    if m.isfile() or m.issym() or m.islnk()]
    total_files = len(file_members)

    # detect single root folder
    root_folders = {Path(m.name).parts[0] for m in members if Path(m.name).parts}
    has_single_root = len(root_folders) == 1
    root_folder = next(iter(root_folders)) if has_single_root else None


    show_progress: bool = progress and task_id is not None
    if show_progress:
        progress.update(task_id, total=total_files)

    # Extract files
    extracted_count = 0
    for member in file_members:
        file_path = Path(member.name)

        # handle single root folder
        if has_single_root and root_folder:
            if file_path.parts[0] == root_folder:
                file_path = file_path.relative_to(root_folder)

        # skip excluded
        if should_exclude(file_path):
            if show_progress:
                progress.update(task_id, advance=1)
            continue

        target_path = install_dir / file_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # regular file
        if member.isfile():
            source = compressed_data.extractfile(member)
            if source:
                target_path.write_bytes(source.read())
            os.chmod(target_path, member.mode)

        # symbolic link
        elif member.issym():
            if target_path.exists() or target_path.is_symlink():
                target_path.unlink()
            target_path.symlink_to(member.linkname)

        # hard link
        elif member.islnk():
            link_target = Path(member.linkname)
            if has_single_root and root_folder and link_target.parts[0] == root_folder:
                link_target = link_target.relative_to(root_folder)
            target_path.hardlink_to(install_dir / link_target)

        # update progress
        if show_progress:
            extracted_count += 1
            progress.update(task_id, advance=1)

