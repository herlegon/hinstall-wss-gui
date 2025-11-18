from pathlib import Path
from tarfile import TarFile, TarInfo
from zipfile import ZipFile
from rich.progress import (
    Progress,
)
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
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
    all_members: list[TarInfo] = []
    root_folders = set()
    total_bytes: int = 0

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

