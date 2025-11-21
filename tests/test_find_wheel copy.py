from pathlib import Path
import platform
import re
from pprint import pprint
import sys

from hytils import lightgreen, red, yellow
sys.path.append(str(Path(__file__).resolve().parent.parent))
from hinstall import ilog


import sys
import platform
import re

def get_python_tags():
    """
    Get all compatible Python tags for this system.
    Returns list in priority order: [('cp312', 'cp312'), ('cp37', 'abi3'), ('py3', 'none'), ...]
    """
    py_ver = sys.version_info
    tags = []

    # 1. Exact version match (e.g., cp312-cp312)
    py_tag = f"cp{py_ver.major}{py_ver.minor}"
    tags.append((py_tag, py_tag))

    # 2. abi3 tags (stable ABI) - from cp32 up to current version
    # Note: abi3 introduced in Python 3.2, but commonly used from 3.6+
    for minor in range(6, py_ver.minor + 1):
        tags.append((f"cp3{minor}", "abi3"))

    # 3. Pure Python tags
    tags.append((f"py{py_ver.major}{py_ver.minor}", "none"))
    tags.append((f"py{py_ver.major}", "none"))
    tags.append(("py2.py3", "none"))

    return tags

def get_platform_tags():
    """
    Get all compatible platform tags for this system.
    Returns list in priority order.
    """
    system = platform.system().lower()
    machine = platform.machine().lower()
    tags = []

    if system == "windows":
        if machine in ("amd64", "x86_64"):
            tags.append("win_amd64")
        elif machine in ("x86", "i386", "i686"):
            tags.append("win32")
        elif machine == "arm64":
            tags.append("win_arm64")

    elif system == "darwin":
        mac_ver = platform.mac_ver()[0]
        if mac_ver:
            parts = mac_ver.split('.')
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
        else:
            major, minor = 10, 9

        if machine == "arm64":
            # arm64 macs need 11.0+
            for v in range(max(11, major), 9, -1):
                tags.append(f"macosx_{v}_0_arm64")
        elif machine in ("x86_64", "amd64"):
            # x86_64 can go back to 10.9
            for maj in range(major, 9, -1):
                if maj >= 11:
                    tags.append(f"macosx_{maj}_0_x86_64")
                else:
                    for min_v in range(minor if maj == major else 15, -1, -1):
                        tags.append(f"macosx_{maj}_{min_v}_x86_64")

    elif system == "linux":
        if machine in ("x86_64", "amd64"):
            arch = "x86_64"
        elif machine in ("aarch64", "arm64"):
            arch = "aarch64"
        elif machine in ("i386", "i686"):
            arch = "i686"
        else:
            arch = machine

        # Add manylinux tags in priority order (newer first)
        tags.extend([
            f"manylinux_2_28_{arch}",
            f"manylinux_2_17_{arch}",
            f"manylinux2014_{arch}",
            f"manylinux_2_12_{arch}",
            f"manylinux2010_{arch}",
            f"manylinux_2_5_{arch}",
            f"manylinux1_{arch}",
            f"linux_{arch}",
        ])

    return tags

def parse_wheel_filename(filename):
    """
    Parse wheel filename into components.
    Returns dict with name, version, python, abi, platforms (list).
    """
    # Format: {name}-{version}(-{build})?-{python}-{abi}-{platform}.whl
    # The name can contain hyphens, so we need to be careful

    if not filename.endswith('.whl'):
        return None

    # Remove .whl extension
    name_part = filename[:-4]

    # Split by hyphen
    parts = name_part.split('-')

    # Need at least 5 parts: name, version, python, abi, platform
    if len(parts) < 5:
        return None

    # The last 3 parts are always python-abi-platform
    platform_str = parts[-1]
    abi = parts[-2]
    python = parts[-3]

    # Everything before that is name-version (possibly with build number)
    # Version starts with a digit
    name_version_parts = parts[:-3]

    # Find where version starts (first part that starts with a digit)
    version_idx = None
    for i, part in enumerate(name_version_parts):
        if part and part[0].isdigit():
            version_idx = i
            break

    if version_idx is None:
        return None

    name = '-'.join(name_version_parts[:version_idx])
    version = '-'.join(name_version_parts[version_idx:])

    # Platform can have multiple tags separated by dots
    platforms = platform_str.split('.')

    return {
        'name': name,
        'version': version,
        'python': python,
        'abi': abi,
        'platforms': platforms,
        'filename': filename
    }



def is_compatible_python(wheel_python):
    """Check if wheel's Python tag is compatible with current Python."""
    py_ver = sys.version_info
    current = (py_ver.major, py_ver.minor)

    # cp312, cp313, etc.
    if wheel_python.startswith('cp'):
        match = re.match(r'cp(\d)(\d+)(t)?', wheel_python)
        if match:
            major = int(match.group(1))
            minor = int(match.group(2))
            return (major, minor) == current

    # py3, py312, etc.
    elif wheel_python.startswith('py'):
        if wheel_python == 'py3':
            return current[0] == 3
        match = re.match(r'py(\d)(\d+)?', wheel_python)
        if match:
            major = int(match.group(1))
            minor = int(match.group(2)) if match.group(2) else None
            if minor is None:
                return major == current[0]
            return (major, minor) == current

    return False

def is_compatible_abi(wheel_abi):
    """Check if wheel's ABI tag is compatible."""
    py_ver = sys.version_info

    # abi3 (stable ABI) - works for Python 3.2+
    if wheel_abi == 'abi3':
        return True

    # none - pure Python
    if wheel_abi == 'none':
        return True

    # cp312, etc - must match exactly
    if wheel_abi.startswith('cp'):
        match = re.match(r'cp(\d)(\d+)(t)?', wheel_abi)
        if match:
            major = int(match.group(1))
            minor = int(match.group(2))
            return (major, minor) == (py_ver.major, py_ver.minor)

    return False


def is_compatible_platform(wheel_platforms, system_platforms):
    """Check if any wheel platform tag matches any system platform tag."""
    # 'any' works everywhere
    if "any" in wheel_platforms:
        return True

    # Check if any wheel platform matches any system platform
    for wp in wheel_platforms:
        if wp in system_platforms:
            return True

    return False


# def find_compatible_wheels(wheel_files):
#     """
#     Find all compatible wheels and rank them.
#     Returns list of (priority, filename) tuples, sorted by priority.
#     """
#     system_platforms = get_platform_tags()

#     # FIX: include universal pure-python tag
#     if "any" not in system_platforms:
#         system_platforms.append("any")

#     compatible = []
#     for filename in wheel_files:
#         wheel = parse_wheel_filename(filename)
#         if not wheel:
#             continue

#         pprint(wheel)

#         if not is_compatible_python(wheel['python']):
#             continue

#         if not is_compatible_abi(wheel['abi']):
#             continue

#         if not is_compatible_platform(wheel['platforms'], system_platforms):
#             continue

#         # Calculate priority (lower is better)
#         priority = 100

#         # Prefer specific python version over abi3 over pure python
#         if wheel['abi'] == 'none':
#             priority += 50
#         elif wheel['abi'] == 'abi3':
#             priority += 20

#         # Prefer platform-specific over 'any'
#         if 'any' in wheel['platforms']:
#             priority += 30

#         compatible.append((priority, filename))

#     return sorted(compatible, key=lambda x: x[0])



def filter_compatible_wheels(releases_data, version):
    """
    Filter wheel files from PyPI releases data to find compatible ones.

    Args:
        releases_data: dict like {'releases': {'1.0.0': [{'filename': '...', ...}]}}
        version: version string like '1.0.0'

    Returns:
        List of file dicts, sorted by compatibility (best first)
    """
    python_tags = get_python_tags()
    platform_tags = get_platform_tags()
    # ilog.debug(f"python_tags")
    # pprint(python_tags)
    # ilog.debug(f"platform_tags")
    # pprint(platform_tags)

    files = []

    for file_info in releases_data['releases'][version]:
        filename = file_info['filename']
        print(filename)

        # Skip non-wheel files
        if not filename.endswith('.whl'):
            continue

        # Parse the wheel filename
        wheel = parse_wheel_filename(filename)
        if not wheel:
            continue
        pprint(wheel)

        # Check if any python/abi combination matches
        python_match = False
        for py_tag, abi_tag in python_tags:
            if wheel['python'] == py_tag and wheel['abi'] == abi_tag:
                python_match = True
                break

        if not python_match:
            continue
        print(lightgreen(f"   python_match: {filename}"))

        # Check if any platform tag matches
        platform_match = False
        for plat_tag in platform_tags:
            if plat_tag in wheel['platforms']:
                platform_match = True
                break

        if not platform_match:
            print(red(f"   ERROR: platform doesn't match: {filename}"))
            continue
        print(lightgreen(f"   platform_match: {filename}"))

        # Add with priority
        priority = 0

        # Python tag priority (lower is better)
        for i, (py_tag, abi_tag) in enumerate(python_tags):
            if wheel['python'] == py_tag and wheel['abi'] == abi_tag:
                priority += i * 10
                break

        # Platform tag priority
        for i, plat_tag in enumerate(platform_tags):
            if plat_tag in wheel['platforms']:
                priority += i
                break

        files.append((priority, file_info))

    # Sort by priority and return file info only
    files.sort(key=lambda x: x[0])
    return [f[1] for f in files]


# Example usage with your code pattern:
def example_usage():
    """Example showing how to use with PyPI data"""

    # Simulated PyPI data structure
    data = {
        'releases': {
            '80.9.0': [
                {'filename': "setuptools-80.9.0-py3-none-any.whl", 'url': "ftgyhuj"},
                {'filename': "setuptools-80.9.0.tar.gz}", 'url': "ftgyhuj"},
                # {'filename': 'psutil-7.1.3-cp37-abi3-win_amd64.whl', 'url': '...'},
                # {'filename': 'psutil-7.1.3-cp36-abi3-manylinux2010_x86_64.manylinux_2_12_x86_64.whl', 'url': '...'},
                # {'filename': 'psutil-7.1.3.tar.gz', 'url': '...'},
            ]
        }
    }

    version = '80.9.0'

    # Old way (your code)
    # platform_tag = get_platform_tag()
    # files = []
    # for f in data['releases'][version]:
    #     filename = f['filename']
    #     if filename.endswith('.whl') and (platform_tag in filename or "-any" in filename):
    #         files.append(f)

    # New way (handles multiple tags correctly)
    files = filter_compatible_wheels(data, version)

    if files:
        print(f"Best match: {files[0]['filename']}")
    else:
        print("No compatible wheel found")

    return files



def main():
    print(f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"System: {platform.system()} {platform.machine()}")

    print(f"\nCompatible tags (in priority order):")
    print("\nPython tags:")
    for i, (py, abi) in enumerate(get_python_tags()[:5], 1):
        print(f"  {i}. {py}-{abi}")

    print(f"\nPlatform tags:")
    for i, tag in enumerate(get_platform_tags()[:10], 1):
        print(f"  {i}. {tag}")

    # if len(sys.argv) > 1:
    #     # Read wheel files from arguments
    #     wheel_files = sys.argv[1:]
    #     print(f"\n\nSearching {len(wheel_files)} wheel files...")

    #     compatible = find_compatible_wheels(wheel_files)

    #     if compatible:
    #         print(f"\nCompatible wheels (best first):")
    #         for i, (priority, filename) in enumerate(compatible, 1):
    #             print(f"  {i}. {filename}")
    #         print(f"\n✓ Best match: {compatible[0][1]}")
    #     else:
    #         print("\n✗ No compatible wheels found")
    # else:

    example_usage()
        # print("\n" + "="*60)
        # print("USAGE EXAMPLES:")
        # print("="*60)
        # print("\n1. Check compatible tags for your system:")
        # print("   python script.py")
        # print("\n2. Find best wheel from a list:")
        # print("   python script.py psutil-7.1.3-*.whl")
        # print("\n3. Use in your code to filter PyPI releases:")
        # print("   See filter_compatible_wheels() function")

if __name__ == "__main__":
    main()#!/usr/bin/env python3
"""
Find which wheel file matches your platform - pure stdlib only.
Handles multiple platform tags in wheel filenames correctly.
"""


