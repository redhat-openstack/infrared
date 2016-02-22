import os.path

import configure
import pytest
import yaml

from tests.test_cwd import utils

our_cwd_setup = utils.our_cwd_setup


def test_unsupported_yaml_constructor(our_cwd_setup):
    from cli.utils import update_settings
    from cli.exceptions import IRYAMLConstructorError
    tester_file = 'IRYAMLConstructorError.yml'
    settings = configure.Configuration.from_dict({})
    with pytest.raises(IRYAMLConstructorError):
        update_settings(settings, os.path.join(utils.TESTS_CWD, tester_file))


def test_placeholder_validator(our_cwd_setup):
    from cli.utils import update_settings
    from cli.exceptions import IRPlaceholderException
    from cli.yamls import Placeholder

    injector = 'placeholder_injector.yml'
    overwriter = 'placeholder_overwriter.yml'

    # Checks that 'IRPlaceholderException' is raised if value isn't been
    # overwritten
    settings = configure.Configuration.from_dict({})
    settings = update_settings(settings,
                               os.path.join(utils.TESTS_CWD, injector))

    assert isinstance(settings['place']['holder']['validator'], Placeholder)
    with pytest.raises(IRPlaceholderException) as exc:
        yaml.safe_dump(settings, default_flow_style=False)
    assert "Mandatory value is missing." in str(exc.value.message)

    # Checks that exceptions haven't been raised after overwriting the
    # placeholder
    settings = update_settings(settings,
                               os.path.join(utils.TESTS_CWD, overwriter))

    assert settings['place']['holder'][
        'validator'] == "'!placeholder' has been overwritten"
    yaml.safe_dump(settings, default_flow_style=False)
