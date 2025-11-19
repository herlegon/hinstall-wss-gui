
from dataclasses import dataclass
from datetime import datetime
from pprint import pprint
import tempfile
from hytils import get_extension, reformat_datetime
from pathlib import Path
import re
import shutil
import requests
from urllib.error import URLError

from .backend_dirs import g_backend_dirs
from .utils import (
    ProgressWrapper,
    check_site_reachable,
    extract_tar_file,
    extract_zip_file,
    get_domain_from_url,
)
from .logger import ilog



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

    # to remove after validation
    response: requests.Response | None = None

    # Downloaded/cached
    downloadable: bool = False
    downloaded: bool = False
    cache_file: Path = None
    do_cache: bool = False

    _use_local_host: bool = False
    _retry_count: int = 3

    def __post_init__(self):
        self.skip = bool(self.filename == '')
        if self.do_cache:
            self.cache_file = g_backend_dirs.cache / self.filename
        else:
            self.cache_file = Path(tempfile.gettempdir()) / "herlegon" / self.filename

    @property
    def retry_count(self) -> int:
        return self._retry_count


    @retry_count.setter
    def retry_count(self, count: int) -> None:
        self._retry_count = count


    @property
    def use_local_host(self) -> bool:
        return self._use_local_host


    @use_local_host.setter
    def use_local_host(self, enable: bool) -> None:
        self._use_local_host = enable


    def _update_cache_file(self) -> Path:
        if self.do_cache:
            self.cache_file = g_backend_dirs.cache / self.filename
        else:
            self.cache_file = Path(tempfile.gettempdir()) / "herlegon" / self.filename
        return self.cache_file


    def update_tag(self) -> None:
        last_modified: str = ""
        self.downloadable: bool = False
        self._update_cache_file()

        if self.use_local_host:
            local_host = g_backend_dirs.local_host
            if local_host and local_host.is_dir():
                # Use local rehost for testing purpose
                local_rehost_fp: Path = local_host / self.filename
                if local_rehost_fp.is_file():
                    dt = datetime.fromtimestamp(local_rehost_fp.stat().st_mtime)
                    formatted_time = dt.strftime("%Y-%m-%dT%H-%M-%S")
                    last_modified = formatted_time
                    ilog.debug(f"use local rehost: {self.name}, {last_modified}")
                    self.size = local_rehost_fp.stat().st_size
                    self.downloadable = True
                else:
                    ilog.warning(f"Asked to use local host, but file {local_rehost_fp} not found")
            else:
                ilog.warning(f"Asked to use local host ({local_host}) but directory doesn't exist")

        else:
            # Get info from host and update package info
            url: str = f"{self.host}/{self.filename}"
            ilog.debug(f"url: {url}")

            reacheable = check_site_reachable(get_domain_from_url(url))
            if reacheable:
                for attempt in range(self.retry_count):
                    response: requests.Response
                    try:
                        response = requests.get(url, stream=True)
                        response.raise_for_status()

                    except (URLError, requests.HTTPError):
                        ilog.warning(f"Host not reachable")
                        if attempt < self.retry_count - 1:
                            continue

                    except requests.exceptions.RequestException as e:
                        if str(e).startswith('404'):
                            ilog.error(f"{self.filename} not found on the host")
                            response = None
                            break
                        else:
                            ilog.error(f"Exception while fetching: {str(e)}")
                        if attempt < self.retry_count - 1:
                            continue

                    if response:
                        self.downloadable = True
                        last_modified: str = reformat_datetime(response.headers['Last-Modified'])
                        self.size = int(response.headers.get('Content-length', 0))
                    self.response = response

        self.tag = (
            f"{self.filename}_{last_modified}"
            if last_modified
            else ""
        )


    def is_up_to_date(self) -> bool | None:
        self.update_tag()

        if not self.install_dir.is_dir():
            self.installed = False
            return False

        # Must be installed and tag must match
        if self.tag:
            tag_fp: Path = self.install_dir / self.tag
            if tag_fp.exists():
                self.installed = True
                ilog.debug(f"{self.name} already installed and up-to-date")
                return True

        return None


    def is_installed(self, up_to_date: bool = True) -> bool | None:
        if up_to_date:
            return self.is_up_to_date()

        if not self.install_dir.is_dir():
            self.installed = False
            return False

        # Iterate over files in the directory
        filename_pattern = re.compile(
            rf"^{self.filename}(_\d{{4}}-\d{{2}}-\d{{2}}T\d{{2}}-\d{{2}}-\d{{2}})"
        )
        tag_exists: bool = False
        for file in self.install_dir.iterdir():
            if (
                file.is_file()
                and file.stat().st_size == 0
                and filename_pattern.match(file.name)
            ):
                tag_exists = True
                break

        if not tag_exists:
            self.installed = False
            return False

        # At least a tag but not sure it's up-to-date
        return tag_exists


    def is_cached(self) -> bool:
        self._update_cache_file()
        ilog.debug(f"Searching cache file: {self.cache_file}")
        tag_fp: Path = g_backend_dirs.cache / self.tag
        if (
            self.tag and tag_fp.exists()
            and self.cache_file.is_file()
            and self.cache_file.stat().st_size == self.size
        ):
            self.downloaded = True
            ilog.debug(f"{self.name} installer cached")
            return True

        return False



    def clean_cache(self) -> None:
        # clean cache of other version
        self._update_cache_file()
        ilog.debug(f"Remove old cache: {self.cache_file}")
        if self.cache_file is None:
            return
        for file in self.cache_file.parent.iterdir():
            if (
                file.is_file()
                and file.name.startswith(self.key)
                and file.name not in (
                    self.tag,
                    self.filename
                )
            ):
                file.unlink()

        if not self.do_cache:
            ilog.debug(f"Remove cached installed files")
            for file in self.cache_file.parent.iterdir():
                if file.is_file() and file.name.startswith(self.key):
                    file.unlink()



    def download_from_local_host(self) -> bool:
        if g_backend_dirs.local_host is None:
            raise ValueError(f"local_host must be defined")

        local_fp: Path = g_backend_dirs.local_host / self.filename
        ilog.debug(f"Copy from local host: {local_fp}")

        if local_fp.exists():
            self._update_cache_file()
            cache_dir = self.cache_file.parent
            cache_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(local_fp, cache_dir)
            (cache_dir / self.tag).touch(exist_ok=True)
            ilog.debug(f"Copied to {cache_dir}")
            self.downloaded = True

        else:
            ilog.error(f"Missing file: {local_fp}")
            self.downloaded = False

        return self.downloaded



    def download_from_host(self) -> bool:

        if not self.tag:
            ilog.error(f"Tag file not valid for package: {self.name}")
            return False

        # Force to false because we clean the cache directories
        self.downloaded = False

        self._update_cache_file()
        tmp_dir = self.cache_file.parent
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tag_file = (tmp_dir / self.tag)
        if tag_file.exists():
            tag_file.unlink()

        ilog.debug(f"Download package: {self.filename}")

        _retry: int = self.retry_count
        while _retry:
            ilog.debug(f"Downloading: {self.name} to {tmp_dir}")
            ilog.info(f"total_size={self.size}")

            with open(self.cache_file, "wb") as f:
                try:
                    self.response.raw.decode_content = True

                    # Update every 512KB
                    wrapper = ProgressWrapper(
                        self.response.raw,
                        task_name=f"[{self.name}][install]",
                        update_threshold=512*1024
                    )

                    # 256KB buffer
                    shutil.copyfileobj(wrapper, f, length=256*1024)
                    # Update any remaining bytes
                    wrapper.flush_progress()

                except Exception as e:
                    ilog.debug(f"[W] Retry download, error: {type(e)}")
                    _retry -= 1

            if _retry == 0:
                ilog.debug(f"[E] failed downloading {self.filename}")
                return False

            _retry = 0

        tag_file.touch()
        self.downloaded = True
        return True



    def install(self) -> bool:
        self.installed = False
        if not self.downloaded:
            ilog.error(f"Cannot install {self.name}. Reason: not downloaded")
            return False

        installed: bool = False

        install_dir = self.install_dir
        ilog.debug(f"Install: {self.name} in {install_dir}")

        self._update_cache_file()
        extension: str = get_extension(str(self.cache_file))
        if install_dir.exists():
            shutil.rmtree(install_dir)
        install_dir.mkdir(parents=True, exist_ok=True)

        exclude: list[str] = []
        if self.key.lower() == 'ffmpeg':
            exclude = ('doc', 'man', 'ffplay')

        if (
            extension in ('.gz', '.xz')
            and str(self.cache_file).endswith(f'.tar{extension}')
        ):
            import tarfile

            task_name = f"[{self.name}][install]"
            compression = extension.lstrip('.')
            try:
                with tarfile.open(self.cache_file, f"r:{compression}") as tar_file:
                    extract_tar_file(
                        tar_file,
                        install_dir=install_dir,
                        exclude=exclude,
                        task_name=task_name
                    )
                    installed = True
            except Exception as e:
                ilog.error(f"Failed to untar {self.cache_file}. Reason: {str(e)}")

        elif extension == '.zip':
            import zipfile

            task_name = f"[{self.name}][install]"
            try:
                with zipfile.ZipFile(self.cache_file, "r") as zip_file:
                    extract_zip_file(
                        zip_file,
                        install_dir=install_dir,
                        exclude=exclude,
                        task_name=task_name,
                    )
                    installed = True
            except Exception as e:
                ilog.error(f"Failed to untar {self.cache_file}. Reason: {str(e)}")

        else:
            shutil.move(self.cache_file, install_dir)

        (install_dir / self.tag).touch()
        self.installed = True

        ilog.debug(f"{self.name} installed in {install_dir}")

        if installed:
            self.clean_cache()

        self.installed = installed

        return installed
