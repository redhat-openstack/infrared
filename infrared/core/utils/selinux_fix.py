import glob
import logging
import os
import shutil
import subprocess
import sys


LOG = logging.getLogger(__name__)


def main():
    try:
        setup_logging()
        ensure_system_selinux()
    except Exception:
        LOG.exception('Error fixing SE Linux bindings')
        sys.exit(1)
    else:
        sys.exit(0)


def setup_logging(script_name=None, level=None):
    script_name = (script_name or
                   os.path.basename(sys.modules['__main__'].__file__))
    level = level or logging.DEBUG
    logging_format = (
        script_name +
        ': %(name)-s: %(levelname)-7s %(asctime)-15s | %(message)s')
    logging.basicConfig(level=level, stream=sys.stderr, format=logging_format)


def ensure_system_selinux():
    try:
        import selinux  # noqa

    except ImportError:
        if has_system_selinux():
            LOG.debug("Make System SE Linux available from '%s'",
                      sys.executable)
            copy_system_selinux()
            return True
        else:
            LOG.debug("System SE Linux not available or installed for '%s'",
                      sys.executable)
            return False
    else:
        LOG.debug("SE Linux is already available for '%s'", sys.executable)
        return True


def copy_system_selinux(force=True):
    try:
        import selinux  # noqa
    except ImportError as e:
        LOG.debug('SE Linux is not available yet')
        new_error = type(e)(str(e) + ". Check that 'libselinux-python' is "
                                     "installed")
        from distutils import sysconfig

        import inspect
        import pydoc

        if hasattr(sys, 'real_prefix'):
            fallback_prefix = sys.real_prefix
        elif hasattr(sys, 'base_prefix'):
            fallback_prefix = sys.base_prefix
        else:
            LOG.error('System SE Linux is not available or installed')
            raise new_error
        LOG.debug("fallback_prefix is '%s'", fallback_prefix)

        # check for venv
        VENV_SITE = sysconfig.get_python_lib()
        PYTHON_LIB_PATH1 = sysconfig.get_python_lib(plat_specific=True,
                                     prefix=fallback_prefix)
        SELINUX_PATH1 = os.path.join(PYTHON_LIB_PATH1,
                                     "selinux")

        PYTHON_LIB_PATH2 = os.path.dirname(inspect.getfile(pydoc))
        SELINUX_PATH2 = os.path.join(PYTHON_LIB_PATH2,
                                     "site-packages/selinux")

        dest = os.path.join(VENV_SITE, "selinux")
        if force:
            shutil.rmtree(dest, ignore_errors=True)
        elif os.path.exists(dest):
            LOG.debug("'%s' already exists'", dest)
            raise new_error

        # filter precompiled files including subdirs
        files = []
        LOG.debug("SELINUX_PATH1: %s" % SELINUX_PATH1)
        LOG.debug("SELINUX_PATH2: %s" % SELINUX_PATH2)

        for path, _, fnames in (*os.walk(SELINUX_PATH1), *os.walk(SELINUX_PATH2)):
            for name in fnames:
                if not os.path.splitext(name)[1] in (".pyc", ".pyo"):
                    files.append(os.path.join(path, name))

        LOG.debug("files: %s" % files)

        # add extra file for (libselinux-python-2.5-9.fc24.x86_64)
        # for python3 we can have extra lines after _selinux names.
        # so need to use glob expression
        _selinux_files1 = glob.glob(os.path.join(PYTHON_LIB_PATH1, "_selinux*.so"))
        _selinux_files2 = glob.glob(os.path.join(PYTHON_LIB_PATH2, "_selinux*.so"))

        if files:
            os.makedirs(dest)

        for f in files:
            LOG.debug("copy file '%s' to '%s'", f, dest)
            shutil.copy(f, dest)

        for _selinux_file in (*_selinux_files1, *_selinux_files2):
            if os.path.exists(_selinux_file):
                LOG.debug("copy file '%s' to '%s'", _selinux_file,
                          os.path.dirname(dest))
                shutil.copy(_selinux_file, os.path.dirname(dest))
        import selinux  # noqa


def has_system_selinux():
    """Checks has system SE Linux bindings

    Import SE Linux bindings from base executable before copying files to
    ensure can actually use SE Linux
    """

    prefix = (getattr(sys, 'real_prefix', None) or
              getattr(sys, 'base_prefix', None) or
              sys.prefix)
    command = 'python{major}.{minor}'.format(major=sys.version_info.major,
                                             minor=sys.version_info.minor)
    executable = os.path.join(prefix, 'bin', command)
    try:
        subprocess.check_call([executable, '-c', 'import selinux'],
                              universal_newlines=True)
    except subprocess.CalledProcessError as ex:
        LOG.debug("System SE Linux not found: %s", ex)
        return False
    return True


if __name__ == '__main__':
    LOG = logging.getLogger(os.path.basename(sys.argv[0]))
    main()
