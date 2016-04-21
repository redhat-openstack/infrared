from tests.test_cwd import utils

our_cwd_setup = utils.our_cwd_setup


def test_get_config_dir_project_defaults(our_cwd_setup):
    from cli import conf
    from cli import utils

    utils.IR_CONF_FILE = 'non_existing_conf.ini'

    conf_file = conf.load_config_file()

    assert 'defaults' in conf_file.sections(),\
        "'defaults' section not in project's default conf file"

    file_default_options = conf_file.options('defaults')
    file_default_options.sort()

    module_default_options = conf.DEFAULT_SECTIONS['defaults'].keys()
    module_default_options.sort()

    assert file_default_options == module_default_options, \
        "Options in conf module and conf file aren't the same"

    from os.path import dirname, join
    for option in conf_file.options('defaults'):
        assert conf_file.get('defaults', option) == join(dirname(dirname(
            __file__)), conf.DEFAULT_SECTIONS['defaults'][option]),\
            "Incorrect Option's (%s) value" % option
