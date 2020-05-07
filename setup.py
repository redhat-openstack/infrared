import setuptools
import importlib

setuptools.setup(
    setup_requires=['pbr'],
    pbr=True)


for module_name in ['platform', 'distro']:
    module = importlib.import_module(module_name)
    linux_distribution = getattr(module, 'linux_distribution', None)
    if linux_distribution:
        break
else:
    def linux_distribution(*_args, **_kwargs):
        return []


if 'redhat' in linux_distribution(supported_dists='redhat',
                                  full_distribution_name=False):
    from infrared.core.utils.selinux_fix import copy_system_selinux
    copy_system_selinux()
