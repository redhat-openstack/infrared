# holds the integration tests for IRSpec
import ConfigParser

import os
import yaml
import pytest

from cli import exceptions


@pytest.fixture(scope='session')
def conf_file(tmpdir_factory):
    """
    Creates a temporary configuration file.
    """
    return tmpdir_factory.mktemp('conf_files').join('conf.ini').strpath


def test_generate_conf_file(conf_file, mock_spec):
    """
    Verify generation of the configuration file.
    """
    mock_spec.run(
        spec_args=['--req=test', '--generate-conf-file=' + conf_file])

    with open(conf_file) as fd:
        config = ConfigParser.ConfigParser()
        config.readfp(fd)
        assert config.has_section(mock_spec.IR_SUB_COMMAND)
        # check options
        # image
        assert config.has_option(mock_spec.IR_SUB_COMMAND, 'image')
        assert config.get(mock_spec.IR_SUB_COMMAND, 'image') == 'default.yml'
        # choice
        assert config.has_option(mock_spec.IR_SUB_COMMAND, 'choice')
        assert config.get(mock_spec.IR_SUB_COMMAND, 'choice') == '2'
        # req
        assert config.has_option(mock_spec.IR_SUB_COMMAND, 'req')
        assert config.get(
            mock_spec.IR_SUB_COMMAND,
            'req') == 'Required argument. Edit with one of the allowed ' \
                      'values OR override with CLI: --req=<option>'
        # optional should not be present
        assert not config.has_option(mock_spec.IR_SUB_COMMAND, 'opt ')


def test_run_from_file(tmpdir, conf_file, mock_spec):
    """
    verify arguments reading from the configuration file.
    """
    out_file = tmpdir.mkdir('out2').join('out2.ini').strpath
    mock_spec.run(
        spec_args=['--req', 'test', '--generate-conf-file=' + conf_file])

    mock_spec.run(spec_args=['--req=test',
                             '--from-file={}'.format(conf_file),
                             '--output={}'.format(out_file)])

    with open(out_file) as fd:
        data = yaml.load(fd)

    assert mock_spec.IR_APP_NAME in data
    app_data = data[mock_spec.IR_APP_NAME]

    # check image yaml data
    assert 'image' in app_data
    assert 'image_file' in app_data['image']
    assert 'image_size' in app_data['image']
    assert app_data['image']['image_file'] == 'file.qcow'
    assert app_data['image']['image_size'] == 555

    # check required argument
    assert 'req' in app_data
    assert app_data['req'] == 'test'

    # check choice
    assert 'choice' in app_data
    assert app_data['choice'] == '2'


def test_required_options(mock_spec):
    """
    Verify all the required arguments need to be provided
    """

    with pytest.raises(exceptions.IRRequiredArgsMissingException) as ex:
        mock_spec.run(spec_args=[])

    assert mock_spec.IR_SUB_COMMAND in ex.value.missing_args
    assert 'req' in ex.value.missing_args[mock_spec.IR_SUB_COMMAND]

    # check we have no exception when calling with required arguments.
    mock_spec.run(spec_args=['--req=123'])


def test_include_common_groups(mock_spec):
    """
    verify included groups of options
    """
    # check there is no exception and common args can be specified
    mock_spec.run(spec_args=['--req=123', '--verbose', '--debug'])
    assert mock_spec.spec_app


def test_require_when_options(mock_spec):
    """
    Verify required_when attribute usage
    """
    with pytest.raises(exceptions.IRRequiredArgsMissingException) as ex:
        mock_spec.run(spec_args=['--req=123', '--images-task=import'])

    assert mock_spec.IR_SUB_COMMAND in ex.value.missing_args
    assert 'images-url' in ex.value.missing_args[mock_spec.IR_SUB_COMMAND]

    # check positive case
    mock_spec.run(spec_args=['--req=123', '--images-task=build'])
    assert mock_spec.spec_app


def test_silent_options(mock_spec):
    """
    Verify the required option can be 'muted'
    """

    mock_spec.run(spec_args=['--do-silent'])
    assert mock_spec.spec_app


def test_unrecognized_options(mock_spec):
    # check invalid option
    with pytest.raises(exceptions.IRUnrecognizedOptionsException) as ex:
        mock_spec.run(spec_args=['--req=123', '--some-odd-option=import'])

    assert 'some-odd-option' in ex.value.wrong_options

    # check that ansible options should work fine
    mock_spec.run(spec_args=['--req=123', '--tags=provision', '--check',
                             '--step', '10', '--become_user=yes'])

    assert 'tags' in mock_spec.spec_app.unknown_args
    assert 'provision' == mock_spec.spec_app.unknown_args['tags']

    assert 'check' in mock_spec.spec_app.unknown_args
    assert mock_spec.spec_app.unknown_args['check']

    assert 'step' in mock_spec.spec_app.unknown_args
    assert '10' == mock_spec.spec_app.unknown_args['step']

    assert 'become_user' in mock_spec.spec_app.unknown_args
    assert mock_spec.spec_app.unknown_args['become_user']


def test_loading_priority(tmpdir_factory, mock_spec):
    """
    Verify arguments gets loaded in priority (env->config file->cli)
    """

    ini_file = tmpdir_factory.mktemp('conf_files').join('priority.ini').strpath

    os.environ['PRIORITY_P1'] = "env_value1"
    os.environ['PRIORITY_P2'] = "env_value2"
    os.environ['PRIORITY_P3'] = "env_value3"
    with open(ini_file, mode='w') as fd:
        fd.write(
            """
[{0}]
priority_p2=file_value2
priority_p1=file_value1

""".format(mock_spec.IR_SUB_COMMAND))
    mock_spec.run(spec_args=['--req=test',
                             '--from-file={}'.format(ini_file),
                             '--priority_p1=cli_value1'])

    assert 'priority_p1' in mock_spec.spec_app.nested_args
    assert mock_spec.spec_app.nested_args['priority_p1'] == 'cli_value1'

    assert 'priority_p2' in mock_spec.spec_app.nested_args
    assert mock_spec.spec_app.nested_args['priority_p2'] == 'file_value2'

    assert 'priority_p3' in mock_spec.spec_app.nested_args
    assert mock_spec.spec_app.nested_args['priority_p3'] == 'env_value3'


def test_nested_controls_options(mock_spec):
    """
    Verify nested and control arguments grouping.
    """
    mock_spec.run(spec_args=['--req=123',
                             '--nested_arg2=value2',
                             '--control_arg1=value3'])

    assert 'req' in mock_spec.spec_app.nested_args
    assert mock_spec.spec_app.nested_args['req'] == '123'
    assert 'req' not in mock_spec.spec_app.control_args

    assert 'nested_arg1' in mock_spec.spec_app.nested_args
    assert mock_spec.spec_app.nested_args['nested_arg1'] == 'defvalue1'
    assert 'nested_arg1' not in mock_spec.spec_app.control_args

    assert 'nested_arg2' in mock_spec.spec_app.nested_args
    assert mock_spec.spec_app.nested_args['nested_arg2'] == 'value2'
    assert 'nested_arg2' not in mock_spec.spec_app.control_args

    assert 'control_arg1' in mock_spec.spec_app.control_args
    assert mock_spec.spec_app.control_args['control_arg1'] == 'value3'
    assert 'control_arg1' not in mock_spec.spec_app.nested_args
