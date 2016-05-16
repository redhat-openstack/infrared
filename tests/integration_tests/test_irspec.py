# holds the integration tests for IRSpec
import ConfigParser
import yaml
import pytest


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
