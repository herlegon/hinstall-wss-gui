
from dataclasses import dataclass
import sys
from typing import Any, Literal



HERLEGON_PACKAGES: tuple[str] = (
    'hutils',
    'hsys',
    'hwidgets',

    # backend is specific for each product,
    # the installation depends on the product name and is stored on the
    # herlegon github repo
    'hbackend',

    # pynnlib must always use the latest release: source only
    'pynnlib',
)



@dataclass
class PyPackage:
    pretty_name: str
    name: str
    variant: str = ""
    version: str = ""
    extra_index_url: str = ""
    wheel: str = ""
    url: str = ""
    size: int = 0
    supported: bool = True
    installed: bool = False
    installed_version: str = ""
    uninstall_before: bool = False
    delayed_install: bool = False
    do_cache: bool = False

    def is_installed(self) -> bool:
        # print(lightcyan(f"[{self.installed_version}] vs [{self.version}]"))
        return bool(self.version == self.installed_version)



class PyPackages(list):

    def __init__(
        self,
        config: dict = None,
        platform: str = ""
    ):
        super().__init__()
        if config:
            if not platform:
                platform = sys.platform
            self._parse_and_populate(config, platform)


    def _parse_and_populate(self, config: dict, platform: str):
        platform_data = (
            config
            .get('py_packages', {})
            .get(platform, {})
            .get('default', {})
        )

        pretty_names: dict[str, str] = platform_data.get('names', {})

        # Process common packages: 1st pass
        common = platform_data.get('common', {})
        if 'pypi' in common:
            for pkg_name in common['pypi']:
                self.append(PyPackage(
                    pretty_name=pretty_names.get(pkg_name, pkg_name),
                    name=pkg_name,
                    version="",
                ))

        # Process delayed packages
        delayed: dict[str, Any] = platform_data.get('delayed', {})
        property_keys: tuple[str] = (
            'extra-index-url',
            'do_cache',
            'uninstall_before',
            'names',
        )

        for category, category_data in delayed.items():
            if not isinstance(category_data, dict):
                continue

            extra_index_url = category_data.get('extra-index-url', delayed.get('extra-index-url', ''))
            do_cache = category_data.get('do_cache', delayed.get('do_cache', False))
            uninstall_before = category_data.get('uninstall_before', delayed.get('uninstall_before', False))

            for key, value in category_data.items():
                key: str
                if key in property_keys:
                    continue

                # Handle nested structures (like torch with cpu/cuda/rocm variants)
                if isinstance(value, dict):
                    for variant, variant_data in value.items():

                        if variant in property_keys:
                            continue
                        variant_extra_index = value.get('extra-index-url', extra_index_url)
                        do_cache = value.get('do_cache', do_cache)
                        uninstall_before = (
                            value.get(
                                'uninstall_before',
                                value.get('uninstall_before', uninstall_before)
                            )
                        )

                        variant: str
                        if not isinstance(variant_data, dict):
                            pkg_name, pkg_version = variant, variant_data
                            if pkg_name not in property_keys:
                                pretty_name = (
                                    pretty_names.get(
                                        f"{pkg_name}-{key}", pretty_names.get(pkg_name, pkg_name)
                                    )
                                    if key
                                    else pretty_names.get(pkg_name, pkg_name)
                                )
                                self.append(
                                    PyPackage(
                                        pretty_name=pretty_name,
                                        variant=key,
                                        name=pkg_name,
                                        version=pkg_version,
                                        extra_index_url=variant_extra_index,
                                        delayed_install=True,
                                        do_cache=do_cache,
                                        uninstall_before=uninstall_before,
                                        supported=False,
                                    )
                                )
                else:
                    # Simple key-value pair
                    pretty_name = (
                        pretty_names.get(
                            f"{pkg_name}-{key}", pretty_names.get(pkg_name, pkg_name)
                        )
                        if key
                        else pretty_names.get(pkg_name, pkg_name)
                    )
                    self.append(
                            PyPackage(
                            pretty_name=pretty_name,
                            name=key,
                            version=value,
                            extra_index_url=extra_index_url,
                            delayed_install=True,
                            do_cache=do_cache,
                            supported=False,
                        )
                    )


    def get_initial(self) -> 'PyPackages':
        result = PyPackages()
        result.extend([pkg for pkg in self if not pkg.delayed_install])
        return result


    def get_delayed(self) -> 'PyPackages':
        """Get all packages marked for delayed installation."""
        result = PyPackages()
        result.extend([pkg for pkg in self if pkg.delayed_install])
        return result



    def get_installed(self) -> 'PyPackages':
        """Get all installed packages."""
        result = PyPackages()
        result.extend([pkg for pkg in self if pkg.installed])
        return result


    def get_not_installed(self) -> 'PyPackages':
        """Get all packages that are not installed."""
        result = PyPackages()
        result.extend([pkg for pkg in self if not pkg.installed])
        return result


    def get_outdated(self) -> 'PyPackages':
        """Get packages where installed version doesn't match required version."""
        result = PyPackages()
        result.extend([pkg for pkg in self if pkg.installed and not pkg.is_installed()])
        return result


    def get_to_uninstall(self) -> 'PyPackages':
        """Get packages marked to uninstall before installing."""
        result = PyPackages()
        result.extend([pkg for pkg in self if pkg.uninstall_before])
        return result


    def find(self, **kwargs) -> 'PyPackages':
        """
        Find packages matching specific criteria.

        Example:
            packages.find(name='torch', delayed_install=True)
            packages.find(installed=False, version='2.9.0+cpu')
        """
        result = PyPackages()
        for pkg in self:
            if all(getattr(pkg, key, None) == value for key, value in kwargs.items()):
                result.append(pkg)
        return result


    def get_pypi_variant_names(self) -> list[str]:
        """Get a list of all package names."""
        names: list[str] = []
        for pkg in self:
            pkg: PyPackage
            names.append(
                f"{pkg.name}-{pkg.variant}" if pkg.variant else pkg.name
            )
        return names


    def get_by_variant(self, variant: Literal['cpu', 'cuda', 'rocm']) -> list[PyPackage]:
        return [pkg for pkg in self if pkg.variant == variant]


    def print_summary(self):
        """Print a summary of the packages."""
        print(f"Total packages: {len(self)}")
        print(f"Standard packages: {len(self.get_standard())}")
        print(f"Delayed packages: {len(self.get_delayed())}")
        print(f"Installed: {len(self.get_installed())}")
        print(f"Not installed: {len(self.get_not_installed())}")
        if self.get_outdated():
            print(f"Outdated: {len(self.get_outdated())}")





