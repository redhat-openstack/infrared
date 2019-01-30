import os
import glob
import sys


def copy_system_selinux(force=True):
    import sys
    try:
        import selinux  # noqa
    except ImportError as e:
        new_error = type(e)(str(e) + ". Check that 'libselinux-python' is "
                                     "installed")
        import shutil
        from distutils import sysconfig

        if hasattr(sys, 'real_prefix'):
            # check for venv
            VENV_SITE = sysconfig.get_python_lib()
            SELINUX_PATH = os.path.join(
                sysconfig.get_python_lib(plat_specific=True,
                                         prefix=sys.real_prefix),
                "selinux")
            dest = os.path.join(VENV_SITE, "selinux")
            if force:
                shutil.rmtree(dest, ignore_errors=True)
            elif os.path.exists(dest):
                raise new_error

            # filter precompiled files including subdirs
            files = []
            for path, _, fnames in os.walk(SELINUX_PATH):
                for name in fnames:
                    if not os.path.splitext(name)[1] in (".pyc", ".pyo"):
                        files.append(os.path.join(path, name))

            # add extra file for (libselinux-python-2.5-9.fc24.x86_64)
            # for python3 we can have extra lines after _selinux names.
            # so need to use glob expression
            root_dest = sysconfig.get_python_lib(
                plat_specific=True, prefix=sys.real_prefix)
            _selinux_files = glob.glob(os.path.join(root_dest, "_selinux*.so"))

            os.makedirs(dest)
            for f in files:
                shutil.copy(f, dest)

            for _selinux_file in _selinux_files:
                if os.path.exists(_selinux_file):
                    shutil.copy(_selinux_file, os.path.dirname(dest))
        else:
            raise new_error
        import selinux  # noqa


if (__name__ == '__main__' and sys.version_info < 3):
    copy_system_selinux()
