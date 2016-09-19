import os


def copy_system_selinux(force=True):
    try:
        print "Try import..."
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
            if force:
                shutil.rmtree(SELINUX_PATH, ignore_errors=True)
            elif os.path.exists(SELINUX_PATH):
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

            dest = os.path.join(VENV_SITE, "selinux")
            os.makedirs(dest)
            for f in files:
                shutil.copy(f, dest)
        else:
            raise new_error


if __name__ == '__main__':
    copy_system_selinux()
    import selinux  # noqa

