import os
import pytest

TESTS_CWD = os.path.dirname(__file__)
SETTINGS_PATH = os.path.join(TESTS_CWD, "settings")


@pytest.yield_fixture
def os_environ():
    """ Backups env var from os.environ and restores it at teardown. """

    from kcli import conf

    backup_flag = False
    if conf.ENV_VAR_NAME in os.environ:
        backup_flag = True
        backup_value = os.environ.get(conf.ENV_VAR_NAME)
    yield os.environ
    if backup_flag:
        os.environ[conf.ENV_VAR_NAME] = backup_value


@pytest.fixture()
def our_cwd_setup(request):
    """ Change cwd to test_cwd dir. Revert to original dir on teardown. """

    bkp = os.getcwd()

    def our_cwd_teardown():
        os.chdir(bkp)

    request.addfinalizer(our_cwd_teardown)
    os.chdir(TESTS_CWD)
