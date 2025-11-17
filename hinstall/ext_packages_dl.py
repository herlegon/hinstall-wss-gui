from datetime import datetime
from pathlib import Path
import requests
import shutil
from rich.progress import (
    Progress,
    TaskID,
)
import tempfile
from hytils import (
    reformat_datetime,
)
from urllib.error import URLError, HTTPError
from .backend_dirs import g_backend_dirs
from .ext_packages import ExtPackage
from .logger import ilog
from .utils import (
    check_site_reachable,
    get_domain_from_url,
)



def clean_cache(package: ExtPackage) -> None:
    # clean cache of other version
    ilog.debug(f"Remove old cache")
    for file in package.cache_file.parent.iterdir():
        if (
            file.is_file()
            and file.name.startswith(package.key)
            and file.name not in (
                package.tag,
                package.filename
            )
        ):
            file.unlink()

    if not package.do_cache:
        ilog.debug(f"Remove cached installed files")
        for file in package.cache_file.parent.iterdir():
            if file.is_file() and file.name.startswith(package.key):
                file.unlink()



def download_package_from_host(
    package: ExtPackage,
    retry: int = 3,
    progress: Progress| None = None,
    task_id: TaskID | None = None,
) -> bool:

    if not package.tag:
        ilog.error(f"Tag file not valid for package: {package.name}")
        return False

    tmp_dir = package.cache_file.parent
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tag_file = (tmp_dir / package.tag)
    if tag_file.exists():
        tag_file.unlink()

    ilog.debug(f"Download package: {package.filename}")

    _retry: int = retry
    while _retry:
        ilog.debug(f"Downloading: {package.name} to {tmp_dir}")
        if progress is not None:
            progress.update(task_id, total=package.size)
            progress.start_task(task_id)

        with open(package.cache_file, "wb") as f:
            try:
                for data in package.response.iter_content(chunk_size=1024):
                    f.write(data)
                    if progress is not None:
                        progress.update(task_id, advance=len(data))
            except Exception as e:
                ilog.debug("[W] Retry download, error: type(e)")
                _retry -= 1
                continue

        if _retry == 0:
            ilog.debug(f"[E] failed downloading {package.filename}")
            return False

        _retry = 0

    tag_file.touch()
    return True



def download_package_from_local_host(package: ExtPackage) -> bool:
    local_fp: Path = g_backend_dirs.local_host / package.filename
    ilog.debug(f"Searching {local_fp}")
    if local_fp.exists():
        cache_dir = package.cache_file.parent
        cache_dir.mkdir(parents=True, exist_ok=True)
        ilog.debug(f"Copy from local host: {local_fp} -> {cache_dir}")
        shutil.copy(local_fp, cache_dir)
        (cache_dir / package.tag).touch(exist_ok=True)
        return True
    return False



def download_package_(
    package: ExtPackage,
    progress: Progress | None = None,
    retry: int = 3,
    use_local_host: bool = False,
    reinstall: bool = False,
) -> ExtPackage:
    last_modified: str = ""
    downloadable: bool = False
    if use_local_host:
        local_host = g_backend_dirs.local_host
        if local_host and local_host.is_dir():
            # Use local rehost for testing purpose
            local_rehost_fp: Path = local_host / package.filename
            if local_rehost_fp.is_file():
                dt = datetime.fromtimestamp(local_rehost_fp.stat().st_mtime)
                formatted_time = dt.strftime("%Y-%m-%dT%H-%M-%S")
                last_modified = formatted_time
                ilog.debug(f"use local rehost: {package.name}, {last_modified}")
                package.size = local_rehost_fp.stat().st_size
            else:
                ilog.warning(f"Asked to use local host, but file {local_rehost_fp} not found")
        else:
            ilog.warning(f"Asked to use local host ({local_host}) but directory doesn't exist")

    else:
        # Get info from host and update package info
        url: str = f"{package.host}/{package.filename}"
        ilog.debug(f"url: {url}")

        reacheable = check_site_reachable(get_domain_from_url(url))
        if reacheable:
            for attempt in range(retry):
                response: requests.Response
                try:
                    response = requests.get(url, stream=True)
                    response.raise_for_status()

                except (URLError, HTTPError):
                    ilog.warning(f"Host not reachable")
                    if attempt < retry - 1:
                        continue

                except requests.exceptions.RequestException as e:
                    if str(e).startswith('404'):
                        ilog.error(f"{package.filename} not found on the host")
                        break
                    else:
                        ilog.error(f"Exception while fetching: {str(e)}")
                    if attempt < retry - 1:
                        continue

                downloadable = True
                last_modified: str = reformat_datetime(response.headers['Last-Modified'])
                package.size = int(response.headers.get('Content-length', 0))
                package.response = response

    package.tag = (
        f"{package.filename}_{last_modified}"
        if last_modified
        else ""
    )
    if package.do_cache:
        package.cache_file = g_backend_dirs.cache / package.filename
    else:
        package.cache_file = Path(tempfile.gettempdir()) / "herlegon" / package.filename
    ilog.debug(f"package: {'\n'.join(str(package).split(','))}")

    # Check if installed: use a timestamp file for this
    if package.tag:
        tag_fp: Path = package.install_dir / package.tag
        if tag_fp.exists():
            package.installed = True
            ilog.debug(f"{package.name} already installed")

            # Remove cache if installed
            if not package.do_cache and not reinstall:
                try:
                    package.cache_file.unlink()
                except:
                    pass
                tag_fp.unlink()

            if not reinstall:
                clean_cache(package=package)
                return package
        else:
            ilog.debug(f"{package.name} not installed yet")
    else:
        ilog.warning(f"{package.name} not tag found ({package.tag})")

    package.installed = False

    # Detect if cached
    ilog.debug(f"Searching cache file: {package.cache_file}")
    tag_fp: Path = g_backend_dirs.cache / package.tag
    if (
        package.tag and tag_fp.exists()
        and package.cache_file.is_file()
        and package.cache_file.stat().st_size == package.size
    ):
        package.downloaded = True
        ilog.debug(f"{package.name} Use cached installer")

    # Use local host to simulate a download
    if (
        not package.downloaded
        and use_local_host
        and g_backend_dirs.local_host
    ):
        package.downloaded = download_package_from_local_host(package=package)

    # Finally download it from host
    if not package.downloaded and downloadable:
        package.downloaded = download_package_from_host(
            package=package,
            progress=progress,
            task_id=progress.add_task(
                "[green] Installing...",
                name=package.name,
                start=False
            ),
            retry=retry
        )

    return package

