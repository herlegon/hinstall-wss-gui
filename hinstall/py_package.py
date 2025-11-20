from dataclasses import dataclass
import platform
from pprint import pprint
import requests
import subprocess
import sys
from urllib.parse import quote, unquote

from .logger import ilog
from .backend_dirs import g_backend_dirs
from .py_packages_install import generate_backend_env



@dataclass
class PyPackage:
    pretty_name: str
    name: str
    variant: str = ""

    # version to install, installed and latest from pypi
    version: str = ""
    installed_version: str = ""
    latest_version: str = ""

    extra_index_url: str = ""
    wheel: str = ""
    wheel_url: str = ""
    size: int = 0
    supported: bool = True
    installed: bool = False
    uninstall_before: bool = False
    delayed_install: bool = False
    do_cache: bool = False

    _retry_count: int = 3


    @property
    def retry_count(self) -> int:
        return self._retry_count


    @retry_count.setter
    def retry_count(self, count: int) -> None:
        self._retry_count = count


    def uninstall(self) -> bool:
        ilog.debug(f"uninstall {self.name}")
        python_exe = str(g_backend_dirs.python_exe)

        pip_command: str = f"{python_exe} -m pip uninstall -y {self.name}"
        try:
            result = subprocess.run(
                pip_command.split(' '),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            result_str = result.stdout.strip()

        except Exception as e:
            ilog.error(f"Unexpected error: {str(e)}")
            return False

        ilog.debug(result_str)
        return True


    def fetch_info_from_pypi(self) -> bool:
        try:
            url = f"https://pypi.org/pypi/{self.name}/json"
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                raise ValueError("package")

        except Exception as e:
            raise ValueError("package")

        data = response.json()
        info = data['info']

        # Update latest version
        self.latest_version = info["version"]

        # Update wheel
        version = self.version if self.version else self.latest_version
        if not version:
            ilog.warning(f"no version")
            return False

        if 'torch' in self.name:
            return True

        if version and version not in data['releases'].keys():
            raise ValueError("version")

        # Pick first wheel file for that version
        wheel_file = None
        for f in data['releases'][version]:
            if f['filename'].endswith('.whl'):
                wheel_file = f
                break

        if not wheel_file:
            raise ValueError("wheel")

        self.wheel = wheel_file['filename']
        self.wheel_url = wheel_file['url']
        self.size = wheel_file['size']

        return True



    def get_wheel_size(self) -> None:
        if not self.wheel_url:
            return
        self.size = 0
        try:
            # HEAD request avoids downloading the file
            response = requests.head(
                self.wheel_url,
                allow_redirects=True,
                timeout=5
            )
            if response.status_code == 200:
                self.size = int(response.headers.get("content-length", 0))

            else:
                ilog.error(f"Failed to get wheel size, status code: {response.status_code}")

        except Exception as e:
            ilog.error(f"exception while getting size: {str(e)}")


    def resolve_torch_wheel(self):
        """
        Determine the correct PyTorch wheel URL and size.
        If version is not set, use latest PyTorch version from PyPI.
        Handles URL encoding for '+' in wheel filenames.
        """
        try:
            # Step 1: Use latest version if none specified
            version = self.version if self.version else self.latest_version
            if not version:
                self.fetch_latest_version()
                version = self.version if self.version else self.latest_version
            if not version:
                ilog.error("No PyTorch version specified or found")
                return

            # Step 2: Python version
            python_version = f"{sys.version_info.major}{sys.version_info.minor}"

            # Step 3: Detect architecture
            sys_platform = sys.platform
            if sys_platform.startswith("win"):
                arch = "win_amd64" if platform.architecture()[0] == "64bit" else "win32"
            elif sys_platform == "darwin":
                arch = "arm64" if platform.machine() == "arm64" else "x86_64"
            elif sys_platform.startswith("linux"):
                arch = "manylinux_2_28_x86_64"  # default Linux x86_64
            else:
                arch = "unknown"

            arch = "win_amd64"
            # Step 4: Construct wheel filename
            wheel_name = f"{self.name}-{version}-cp{python_version}-cp{python_version}-{arch}.whl"

            # URL encode '+' in the version string
            if '+' in version:
                version, compute_platform = version.split('+')
            else:
                compute_platform = 'cpu'

            wheel_url = f"https://download.pytorch.org/whl/{compute_platform}/{quote(wheel_name)}"

            # Step 5: Check wheel existence (HEAD request)
            response = requests.head(wheel_url, allow_redirects=True, timeout=10)
            if response.status_code == 200:
                self.size = int(response.headers.get("content-length", 0))
                self.wheel_url = wheel_url
                self.wheel = wheel_name
                # print(f"Found PyTorch wheel: {wheel_name}, size: {self.size / (1024**2):.2f} MB")
                return True
            else:
                ilog.error(f"Wheel not found: {wheel_url}, status: {response.status_code}")
                return

        except Exception as e:
            ilog.error(f"Error resolving PyTorch wheel: {str(e)}")
            return


    def resolve_tensorrt_wheel(self) -> bool:
        """Get TensorRT wheel URL from NVIDIA's index."""
        python_exe = str(g_backend_dirs.python_exe)

        # TensorRT is hosted on NVIDIA's PyPI index
        nvidia_index = "https://pypi.nvidia.com"

        # Set the extra_index_url if not already set
        if not self.extra_index_url:
            self.extra_index_url = nvidia_index

        version_spec = f"=={self.version}" if self.version else ""

        # Use pip download to get the URL
        cmd = [
            python_exe, "-m", "pip", "download",
            "--no-deps",
            "--no-cache-dir",
            "--index-url", self.extra_index_url,
            f"{self.name}{version_spec}",
            "--progress-bar", "off",
        ]

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=generate_backend_env(),
            )

            import re
            url_pattern = re.compile(r'(https?://[^\s]+\.whl)')

            for line in iter(proc.stdout.readline, ''):
                line = line.strip()
                print(line)  # Debug output

                # Found URL - terminate immediately
                if match := url_pattern.search(line):
                    proc.terminate()
                    self.url = match.group(1)
                    self.wheel = unquote(self.url.split('/')[-1])

                    # Parse version from wheel name
                    parts = self.wheel.split('-')
                    if len(parts) >= 2:
                        self.version = parts[1]

                    # Get size
                    import requests
                    try:
                        resp = requests.head(self.url, timeout=10, allow_redirects=True)
                        self.size = int(resp.headers.get('content-length', 0))
                    except:
                        self.size = 0

                    ilog.info(f"Found {self.pretty_name}: {self.wheel}")
                    ilog.info(f"URL: {self.url}")
                    ilog.info(f"Size: {self.size / 1024**2:.1f} MB")
                    return True

                # Check for errors
                if "No matching distribution found" in line:
                    proc.terminate()
                    self.supported = False
                    ilog.warning(f"[W] {self.pretty_name} not supported on this platform")
                    return False

                if "could not find a version" in line.lower():
                    proc.terminate()
                    ilog.error(f"Version {self.version} not found for {self.name}")
                    return False

            proc.wait(timeout=30)
            return False

        except subprocess.TimeoutExpired:
            proc.kill()
            ilog.error(f"Timeout for {self.name}")
            return False
        except Exception as e:
            ilog.error(f"Error: {e}")
            return False


    def update_info(self):
        if 'torch' in self.name:
            self.resolve_torch_wheel()
            self.get_wheel_size()

        # elif 'tensorrt' in self.name:
        #     # self.get_tensorrt_wheel_url()
        #     return

        else:
            try:
                self.fetch_info_from_pypi()

            except Exception as e:
                exception = str(e)
                if 'version' in exception:
                    # Version not found, use latest
                    ilog.error(f"Version not found for {self.name}, use latest")
                    self.version = ""
                    self.update_info()

                elif 'wheel' in exception:
                    ilog.critical(f"Wheel not found for {self.name}")

                elif 'package' in exception:
                    ilog.critical(f"Package {self.name} not found on pypi")

                return


    def _fast_pip_download(self) -> bool:
        """Quick pip download with early termination."""
        python_exe = str(g_backend_dirs.python_exe)
        index_url = ["--index-url", self.extra_index_url] if self.extra_index_url else []
        version_spec = f"=={self.version}" if self.version else ""

        cmd = [
            python_exe, "-m", "pip", "download",
            "--no-deps", "--no-cache-dir",
            f"{self.name}{version_spec}",
            *index_url,
            "--progress-bar", "off",
        ]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        import re
        url_pattern = re.compile(r'(https?://[^\s]+\.whl)')

        try:
            for line in iter(proc.stdout.readline, ''):
                if match := url_pattern.search(line):
                    proc.terminate()
                    self.wheel_url = match.group(1)
                    self.wheel = unquote(self.wheel_url.split('/')[-1])
                    self.version = self.wheel.split('-')[1]

                    import requests
                    resp = requests.head(self.wheel_url, timeout=10, allow_redirects=True)
                    self.size = int(resp.headers.get('content-length', 0))
                    return True

                if "No matching distribution" in line:
                    proc.terminate()
                    self.supported = False
                    return False

            proc.wait(timeout=15)
        except:
            proc.kill()

        return False


