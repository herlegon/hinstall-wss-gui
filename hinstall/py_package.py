
from dataclasses import dataclass
import json
from pathlib import Path
import platform
from pprint import pprint
import re
import subprocess
import sys
import time
from typing import Any, Literal
from urllib.parse import unquote

import requests

from hytils import lightcyan, lightgreen, red, yellow

from .backend_dirs import g_backend_dirs
from .logger import ilog



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
    url: str = ""
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


    def get_latest_version(self):
        # ilog.debug(f"[{self.name}]: get version")
        url = f"https://pypi.org/pypi/{self.name}/json"
        r = requests.get(url)
        if r.status_code != 200:
            ilog.debug(f"[{self.name}]: Failed to get version")
            return
        data = r.json()
        self.latest_version = data["info"]["version"]


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



    def update_wheel_url(self) -> bool:
        """Fast method using PyPI API with simple compatibility check."""
        python_exe = str(g_backend_dirs.python_exe)

        # Check if installed
        if subprocess.run([python_exe, "-m", "pip", "show", self.name],
                        capture_output=True).returncode == 0:
            self.installed = True
            ilog.info(f"{self.pretty_name} already installed")
            return True

        # For custom index, use pip
        if self.extra_index_url and 'pypi.org' not in self.extra_index_url:
            return self._fast_pip_download()

        try:
            # Get from PyPI
            import requests
            url = f"https://pypi.org/pypi/{self.name}/json"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            target_version = self.version if self.version else data['info']['version']

            if target_version not in data['releases']:
                ilog.error(f"Version {target_version} not found")
                return False

            # Get system info for compatibility
            py_version = f"cp{sys.version_info.major}{sys.version_info.minor}"
            system = platform.system().lower()
            machine = platform.machine().lower()

            # Map machine to wheel tags
            if 'amd64' in machine or 'x86_64' in machine:
                arch = 'amd64' if system == 'windows' else 'x86_64'
            elif 'arm64' in machine or 'aarch64' in machine:
                arch = 'arm64'
            else:
                arch = machine

            # Look for compatible wheel
            releases = data['releases'][target_version]

            # Try to find best match
            for file_info in releases:
                if file_info['packagetype'] == 'bdist_wheel':
                    wheel_name = file_info['filename']

                    # Check if wheel is compatible (simple heuristic)
                    if (py_version in wheel_name and
                        (arch in wheel_name.lower() or 'any' in wheel_name)):

                        self.url = file_info['url']
                        self.wheel = wheel_name
                        self.version = target_version
                        self.size = file_info['size']
                        ilog.info(f"Found {self.pretty_name}: {self.wheel}")
                        return True

            # Try universal wheels
            for file_info in releases:
                if file_info['packagetype'] == 'bdist_wheel':
                    wheel_name = file_info['filename']
                    if 'py3-none-any' in wheel_name or 'py2.py3-none-any' in wheel_name:
                        self.url = file_info['url']
                        self.wheel = wheel_name
                        self.version = target_version
                        self.size = file_info['size']
                        ilog.info(f"Found {self.pretty_name}: {self.wheel}")
                        return True

            ilog.warning(f"No compatible wheel found for {self.name}")
            self.supported = False
            return False

        except Exception as e:
            ilog.error(f"Error: {e}")
            return False

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
                    self.url = match.group(1)
                    self.wheel = unquote(self.url.split('/')[-1])
                    self.version = self.wheel.split('-')[1]

                    import requests
                    resp = requests.head(self.url, timeout=10, allow_redirects=True)
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


















    def get_wheel_url_fast(self) -> bool:
        """Simplified version for pip 25.3."""
        python_exe = str(g_backend_dirs.python_exe)

        # # Check if installed
        # if subprocess.run([python_exe, "-m", "pip", "show", self.name],
        #                 capture_output=True).returncode == 0:
        #     self.installed = True
        #     ilog.info(f"{self.pretty_name} already installed")
        #     return True

        # Build command
        index_url = ["--index-url", self.extra_index_url] if self.extra_index_url else []
        version_spec = f"=={self.version}" if self.version else ""

        cmd = [
            python_exe, "-m", "pip", "install",
            "--dry-run", "--ignore-installed", "--no-deps",
            "--report", "-",
            f"{self.name}{version_spec}",
            *index_url,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=30, check=True)
            print(result)
            report = json.loads(result.stdout)
            pprint(report)

            if report.get('install'):
                pkg = report['install'][0]
                self.url = pkg['download_info']['url']
                self.wheel = unquote(self.url.split('/')[-1])
                self.version = pkg['metadata']['version']

                # Get size
                import requests
                resp = requests.head(self.url, timeout=10, allow_redirects=True)
                self.size = int(resp.headers.get('content-length', 0))

                ilog.info(f"Found {self.pretty_name}: {self.wheel}")
                return True

        except subprocess.CalledProcessError as e:
            if "No matching distribution" in (e.stdout + e.stderr):
                self.supported = False
                ilog.warning(f"{self.pretty_name} not supported on this platform")
        except Exception as e:
            ilog.error(f"Error: {e}")

        return False




    # def update_wheel_url(self) -> bool:
    #     python_exe = str(g_backend_dirs.python_exe)

    #     timeout: float = 5
    #     _retry: int = self.retry_count
    #     if self.extra_index_url:
    #         regex: re.Pattern = re.compile(
    #             rf".*Downloading\s*(https:\/\/.*\/.*\.whl)"
    #         )
    #     else:
    #         regex: re.Pattern = re.compile(
    #             rf".*{self.name}.*(https:\/\/.*\/.*\.whl)\.metadata"
    #         )

    #     already_installed_regex = re.compile(
    #         rf".*Requirement\s*already\s*satisfied:\s*{self.name}"
    #     )
    #     url: str = ""

    #     start_time: float = time.time()
    #     index_url: list[str] = (
    #         ["--index-url", self.extra_index_url]
    #         if self.extra_index_url
    #         else []
    #     )
    #     version = f"=={self.version}" if self.version != '' else ''
    #     pip_command: list[str] = [
    #         python_exe,
    #         "-m", "pip", "download",
    #         # "--no-deps",
    #         "--no-cache-dir",
    #         f"{self.name}{version}",
    #         *index_url,
    #         "--progress-bar=off",
    #         "-vvv"
    #     ]
    #     pip_command = list([x for x in pip_command if x != '' and x is not None])
    #     # print(' '.join(pip_command))
    #     while _retry > 0 and url == '' and not self.installed and self.supported:
    #         sub_process = subprocess.Popen(
    #             pip_command,
    #             stdout=subprocess.PIPE,
    #             stderr=subprocess.STDOUT
    #         )

    #         start_time = time.time()
    #         while (
    #             (time.time() - start_time) < timeout + (self.retry_count - _retry) * 5
    #             and sub_process.poll() is None
    #         ):
    #             try:
    #                 line = sub_process.stdout.readline().decode('utf-8').strip()
    #             except:
    #                 break
    #             if self.name == 'torch':
    #                 # and line.startswith("Obtaining dependency information"):
    #                 print(lightcyan(line))

    #             # if _retry < retry:
    #             #     ilog.debug(line)

    #             if (result := re.search(regex, line)):
    #                 sub_process.terminate()
    #                 url = result.group(1)
    #                 break

    #             if (result := re.search(already_installed_regex, line)):
    #                 sub_process.terminate()
    #                 self.installed = True
    #                 break

    #             if "No matching distribution found" in line:
    #                 sub_process.terminate()
    #                 self.supported = False
    #                 ilog.warning(f"[W] {self.pretty_name} is not supported on this platform")
    #                 break

    #         if url == '' or self.installed:
    #             if sub_process.poll() is None:
    #                 sub_process.terminate()
    #             while sub_process.poll() is None and (time.time() - start_time) > 2:
    #                 time.sleep(0.5)

    #             if not self.installed and self.supported:
    #                 _retry -= 1
    #                 timeout += (self.retry_count - _retry) * 5
    #                 ilog.warning(f"retry: {_retry}, new timeout: timeout")

    #     self.url = url
    #     if self.url == '' and not self.installed and self.supported:
    #         ilog.error(red(f"[E] Failed  to fetch url for {self.name}"))

    #     elif self.installed:
    #         ilog.info(f"{self.pretty_name} already installed")

    #     elif self.url != '':
    #         self.wheel = unquote(self.url.split('/')[-1])
    #         self.version = unquote(self.wheel.split('-')[1])
    #         response: requests.Response
    #         try:
    #             response = requests.get(self.url, stream=True)
    #             response.raise_for_status()
    #         except requests.exceptions.RequestException as e:
    #             if str(e).startswith('404'):
    #                 ilog.error(f"File {self.url} not found")
    #             return False
    #         self.size=int(response.headers.get('Content-length', 0))

    #     return True

