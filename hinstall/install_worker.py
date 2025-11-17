from pprint import pprint
import sys
import os
import subprocess
import json
import zipfile
import shutil
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from PySide6.QtCore import QThread, Signal

from .backend_dirs import (
    BackendDirectories,
    # get_python_version,
)


python_version: str = "3.12"


class InstallWorker(QThread):
    """Worker thread for backend installation/update"""
    progress = Signal(str)  # Status message
    finished = Signal(bool, str)  # Success, message

    def __init__(
        self,
        backend_dirs: BackendDirectories,
        keep_installers: bool = False,
        use_local_rehost: bool = False
    ):
        super().__init__()

        # Pass the dirs as an argument because it may have been patch for
        # the local package directories
        # to use the local directory rather than downloading
        self.backend_dirs = backend_dirs

        self.python_exe = None
        self.max_retries = 3

        self.use_local = True
        self.keep_installers = keep_installers


    def run(self):
        backend_dirs = self.backend_dirs
        pprint(backend_dirs)


        # 1. Verify python installation: get version
        python_dir: Path = backend_dirs.app / "python"
        if sys.platform == 'win32':
            python_exe: Path = python_dir / "python.exe"
        elif sys.platform == 'linux':
            python_exe: Path = python_dir / "python"

        print(f"python version: {get_python_version(python_exe)}")
        if get_python_version(python_exe) != python_version:
            print("install python")



        # 2. Verify python packages: use a list of PyPackage
        # @dataclass
        # class PyPackage:
        #     pretty_name: str
        #     name: str
        #     version: str = ""
        #     index_url: str = ""
        #     wheel: str = ""
        #     url: str = ""
        #     size: int = 0
        #     supported: bool = True
        #     installed: bool = False
        #     installed_version: str = ""
        #     uninstall_before: bool = False
        #     delay_install: bool = False


        # 3. List the missing packages or outdated

        # 4. Install all packages except some that are dependent of the system

        # 5. Create an additional list of PyPackage that have to be installed
        #       torch cuda If a cuda gpu available else cpu
        #       tensorrt if cuda is available

        # 6. Install













        # try:
        # Create cache directory if keeping installers
        cache_dir: Path = backend_dirs.cache
        if self.keep_installers and cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"created cache_dir: {cache_dir}")

        # Check if we should use local packages
        rehost_dir: Path = backend_dirs.local_host
        if rehost_dir and rehost_dir.exists():
            self.progress.emit("Local rehost directory found, using local installation...")
            self.use_local = True
        else:
            self.progress.emit("Local rehost not found, using internet connection...")
            self.use_local = False

        # Check if backend already exists
        self.python_exe = backend_dirs.app / "python" / "python.exe"



        is_update = self.python_exe.exists()

        if is_update:
            self.progress.emit("Checking for updates...")
            self._check_updates()
        else:
            self.progress.emit("Installing backend...")
            self._install_backend()

        self.finished.emit(True, "Installation/Update completed successfully!")

        # except Exception as e:
        #     self.finished.emit(False, f"Installation failed: {str(e)}")


    def _download_with_retry(self, url, desc):
        """Download with retry mechanism"""
        for attempt in range(self.max_retries):
            try:
                self.progress.emit(f"{desc} (attempt {attempt + 1}/{self.max_retries})...")
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urlopen(req, timeout=30) as response:
                    return response.read()
            except (URLError, HTTPError) as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Failed to download {desc} after {self.max_retries} attempts: {e}")
        return None


    def _get_file_local_or_download(self, local_filename, download_url, desc):
        """Get file from local directory or download from internet"""

        # First check cache if we're keeping installers
        cache_dir: Path = self.backend_dirs['cache']
        if cache_dir and cache_dir.exists():
            cache_path = cache_dir / local_filename
            if cache_path.exists():
                self.progress.emit(f"Using cached {desc}...")
                return cache_path.read_bytes()

        # Then check local packages directory
        if self.use_local:
            local_path = cache_dir / local_filename
            if local_path.exists():
                self.progress.emit(f"Using local {desc}...")
                data = local_path.read_bytes()
                # Save to cache if keeping installers
                if cache_dir:
                    cache_path = cache_dir / local_filename
                    cache_path.write_bytes(data)
                return data
            else:
                self.progress.emit(f"Local {desc} not found, downloading...")

        # Download from internet
        data = self._download_with_retry(download_url, desc)

        # Save to cache if keeping installers
        if cache_dir and data:
            cache_path = cache_dir / local_filename
            cache_path.write_bytes(data)
            self.progress.emit(f"Cached {desc} for future use")

        return data

    def _check_site_reachable(self, url):
        """Check if site is reachable with retries"""
        for attempt in range(self.max_retries):
            try:
                req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                urlopen(req, timeout=10)
                return True
            except (URLError, HTTPError):
                if attempt < self.max_retries - 1:
                    continue
        return False

    def _install_backend(self):
        """Install backend from scratch"""
        self.backend_dirs.mkdir(parents=True, exist_ok=True)

        # Download Python embeddable
        python_filename = f"python-{self.python_version}-embed-amd64.zip"
        python_url = f"https://www.python.org/ftp/python/{self.python_version}/{python_filename}"

        if not self.use_local:
            self.progress.emit("Checking Python download site...")
            if not self._check_site_reachable("https://www.python.org"):
                raise Exception("Python.org is not reachable")

        self.progress.emit("Getting Python embeddable...")
        python_zip = self._get_file_local_or_download(python_filename, python_url, "Python embeddable")

        python_dir = self.backend_dir / "python"
        python_dir.mkdir(exist_ok=True)

        self.progress.emit("Extracting Python...")
        zip_path = self.backend_dir / "python.zip"
        with open(zip_path, 'wb') as f:
            f.write(python_zip)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(python_dir)

        zip_path.unlink()

        # Enable site-packages by editing pythonXXX._pth
        self._enable_site_packages(python_dir)

        # Download and install pip
        self.progress.emit("Installing pip...")
        self._install_pip(python_dir)

        # Install required packages
        self._install_packages()

        # Download pynnlib
        self._install_pynnlib()

    def _enable_site_packages(self, python_dir):
        """Enable site-packages in embedded Python"""
        for pth_file in python_dir.glob("python*._pth"):
            content = pth_file.read_text()
            if "#import site" in content:
                content = content.replace("#import site", "import site")
                pth_file.write_text(content)
            elif "import site" not in content:
                pth_file.write_text(content + "\nimport site\n")
            break



    def _install_packages(self):
        """Install required Python packages"""
        packages = ["websockets", "aiohttp"]  # Add your required packages

        if self.use_local:
            # Check for wheel files in local directory
            for pkg in packages:
                self.progress.emit(f"Installing {pkg}...")
                # Look for wheel files matching the package name
                wheel_files = list(local_packages.glob(f"{pkg}*.whl"))

                if wheel_files:
                    # Install from local wheel
                    self.progress.emit(f"Using local wheel for {pkg}...")
                    subprocess.run([str(self.python_exe), "-m", "pip", "install", str(wheel_files[0])],
                                 check=True, capture_output=True)
                else:
                    # Fall back to internet
                    self.progress.emit(f"Local wheel not found for {pkg}, downloading...")
                    subprocess.run([str(self.python_exe), "-m", "pip", "install", pkg],
                                 check=True, capture_output=True)
        else:
            # Install from internet
            for pkg in packages:
                self.progress.emit(f"Installing {pkg}...")
                subprocess.run([str(self.python_exe), "-m", "pip", "install", pkg],
                             check=True, capture_output=True)

    def _install_pynnlib(self):
        """Download and install pynnlib from GitHub or local"""
        if self.use_local:
            # Check for local pynnlib zip
            local_pynnlib = list(local_packages.glob("pynnlib*.zip"))

            if local_pynnlib:
                self.progress.emit("Using local pynnlib...")
                pynnlib_zip = local_pynnlib[0].read_bytes()
                version = "local"
            else:
                self.progress.emit("Local pynnlib not found, downloading from GitHub...")
                pynnlib_zip, version = self._download_pynnlib_from_github()
        else:
            pynnlib_zip, version = self._download_pynnlib_from_github()

        # Extract pynnlib
        pynnlib_path = self.backend_dir / "pynnlib.zip"
        with open(pynnlib_path, 'wb') as f:
            f.write(pynnlib_zip)

        self.progress.emit("Extracting pynnlib...")
        extract_dir = self.backend_dir / "pynnlib_temp"
        with zipfile.ZipFile(pynnlib_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Find the actual directory (GitHub adds a prefix)
        extracted = list(extract_dir.iterdir())[0]
        target_dir = self.backend_dir / "pynnlib"

        if target_dir.exists():
            shutil.rmtree(target_dir)

        shutil.move(str(extracted), str(target_dir))
        shutil.rmtree(extract_dir)
        pynnlib_path.unlink()

        # Save version info
        version_file = self.backend_dir / "pynnlib_version.txt"
        version_file.write_text(version)

    def _download_pynnlib_from_github(self):
        """Download pynnlib from GitHub"""
        self.progress.emit("Checking GitHub...")
        if not self._check_site_reachable("https://api.github.com"):
            raise Exception("GitHub is not reachable")

        # Get latest release
        self.progress.emit("Fetching pynnlib latest release...")
        api_url = "https://api.github.com/repos/YOUR_USERNAME/pynnlib/releases/latest"

        try:
            release_data = self._download_with_retry(api_url, "pynnlib release info")
            release_info = json.loads(release_data)
            download_url = release_info['zipball_url']
            version = release_info['tag_name']
        except:
            # Fallback to main branch
            self.progress.emit("No release found, using main branch...")
            download_url = "https://github.com/YOUR_USERNAME/pynnlib/archive/refs/heads/main.zip"
            version = "main"

        self.progress.emit(f"Downloading pynnlib ({version})...")
        pynnlib_zip = self._download_with_retry(download_url, "pynnlib")

        return pynnlib_zip, version

    def _check_updates(self):
        """Check for updates of packages and pynnlib"""
        # Check pynnlib updates
        self.progress.emit("Checking pynnlib updates...")

        version_file = self.backend_dir / "pynnlib_version.txt"
        current_version = version_file.read_text().strip() if version_file.exists() else "unknown"

        if self.use_local:
            self.progress.emit("Using local mode, skipping online update check")
        elif not self._check_site_reachable("https://api.github.com"):
            self.progress.emit("GitHub not reachable, skipping pynnlib update check")
        else:
            try:
                api_url = "https://api.github.com/repos/YOUR_USERNAME/pynnlib/releases/latest"
                release_data = self._download_with_retry(api_url, "latest release info")
                release_info = json.loads(release_data)
                latest_version = release_info['tag_name']

                if latest_version != current_version:
                    self.progress.emit(f"Updating pynnlib from {current_version} to {latest_version}...")
                    self._install_pynnlib()
                else:
                    self.progress.emit("pynnlib is up to date")
            except:
                self.progress.emit("Could not check pynnlib updates")

        # Update packages
        if not self.use_local:
            packages = ["websockets", "aiohttp"]  # Your packages
            for pkg in packages:
                self.progress.emit(f"Updating {pkg}...")
                try:
                    subprocess.run([str(self.python_exe), "-m", "pip", "install", "--upgrade", pkg],
                                 check=True, capture_output=True)
                except:
                    self.progress.emit(f"Could not update {pkg}")
        else:
            self.progress.emit("Using local mode, skipping package updates")

