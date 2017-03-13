import os


def copy_system_selinux(force=True):
    try:
        print("Try import...")
        import selinux
    except ImportError as e:
        new_error = type(e)(e.message + ". check that 'python-libselinux is "
                                        "installed'")
        import sys
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

            # filter precompiled files
            files = [os.path.join(SELINUX_PATH, f)
                     for f in os.listdir(SELINUX_PATH)
                     if not os.path.splitext(f)[1] in (".pyc", ".pyo")]

            # add extra file for (libselinux-python-2.5-9.fc24.x86_64)
            _selinux_file = os.path.join(
                sysconfig.get_python_lib(plat_specific=True,
                                         prefix=sys.real_prefix),
                "_selinux.so")
            if os.path.exists(_selinux_file):
                files.append(_selinux_file)

            os.makedirs(dest)
            for f in files:
                shutil.copy(f, dest)

            # add extra file for (libselinux-python-2.5-13.fc25.x86_64)
            _selinux_file = os.path.join(
                sysconfig.get_python_lib(plat_specific=True,
                                         prefix=sys.real_prefix),
                "_selinux.so")
            if os.path.exists(_selinux_file):
                shutil.copy(_selinux_file, os.path.dirname(dest))
        else:
            raise new_error
        import selinux  # noqa

if __name__ == '__main__':
    copy_system_selinux()
    # import selinux  # noqa
