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


def test_placeholder_double_validator(our_cwd_setup):
    from cli.utils import update_settings
    from cli.exceptions import IRPlaceholderException
    from cli.yamls import Placeholder

    injector = 'placeholder_double_injector.yml'

    # Checks that 'IRPlaceholderException' is raised if value isn't been
    # overwritten
    settings = configure.Configuration.from_dict({})
    settings = update_settings(settings,
                               os.path.join(utils.TESTS_CWD, injector))

    assert isinstance(settings['place']['holder']['validator1'], Placeholder)
    assert isinstance(settings['place']['holder']['validator2'], Placeholder)
    with pytest.raises(IRPlaceholderException) as exc:
        yaml.safe_dump(settings, default_flow_style=False)


@pytest.mark.parametrize('our_cwd_setup, lookup_style', [
    (our_cwd_setup, 'old'),
    (our_cwd_setup, 'new'),
])
def test_lookup(our_cwd_setup, lookup_style):
    import cli.yamls

    tester_file_name = 'lookup_%s_style.yml' % lookup_style
    tester_file = os.path.join(utils.TESTS_CWD, tester_file_name)

    # load settings from yaml and set them into Lookup 'settings' class var
    cli.yamls.Lookup.settings = configure.Configuration().from_file(
        tester_file).configure()

    if lookup_style == 'new':
        # explicitly call 'in_string_lookup' in order to create Lookup objects
        cli.yamls.Lookup.in_string_lookup()

    # dump the settings in order to retrieve the key's value and load them
    # again for value validation
    settings = yaml.safe_load(
        yaml.safe_dump(cli.yamls.Lookup.settings, default_flow_style=False))

    assert settings['foo']['key_to_be_found'] == "key was found"


@pytest.mark.parametrize('our_cwd_setup, lookup_style', [
    (our_cwd_setup, 'old'),
    (our_cwd_setup, 'new'),
])
def test_lookup_non_existing_key(our_cwd_setup, lookup_style):
    import cli.yamls
    from cli.exceptions import IRKeyNotFoundException

    tester_file_name = 'lookup_%s_style_non_existing_key.yml' % lookup_style
    tester_file = os.path.join(utils.TESTS_CWD, tester_file_name)

    # load settings from yaml and set them into Lookup 'settings' class var
    cli.yamls.Lookup.settings = configure.Configuration().from_file(
        tester_file).configure()

    if lookup_style == 'new':
        # explicitly call 'in_string_lookup' in order to create Lookup objects
        cli.yamls.Lookup.in_string_lookup()

    # dump the settings with the non-existing key and expecting
    # IRKeyNotFoundException to be raised
    with pytest.raises(IRKeyNotFoundException):
        yaml.safe_dump(cli.yamls.Lookup.settings, default_flow_style=False)


@pytest.mark.parametrize('our_cwd_setup, lookup_style', [
    (our_cwd_setup, 'old'),
    (our_cwd_setup, 'new'),
])
def test_nested_lookup(our_cwd_setup, lookup_style):
    import cli.yamls

    tester_file_name = 'lookup_%s_style_nested.yml' % lookup_style
    tester_file = os.path.join(utils.TESTS_CWD, tester_file_name)

    # load settings from yaml and set them into Lookup 'settings' class var
    cli.yamls.Lookup.settings = configure.Configuration().from_file(
        tester_file).configure()

    if lookup_style == 'new':
        # explicitly call 'in_string_lookup' in order to create Lookup objects
        cli.yamls.Lookup.in_string_lookup()

    # dump the settings in order to retrieve the key's value and load them
    # again for value validation
    settings = yaml.safe_load(
        yaml.safe_dump(cli.yamls.Lookup.settings, default_flow_style=False))

    assert settings['foo']['test1'] == "key was found"


@pytest.mark.parametrize('our_cwd_setup, lookup_style', [
    (our_cwd_setup, 'old'),
    (our_cwd_setup, 'new'),
])
def test_recursive_lookup(our_cwd_setup, lookup_style):
    import cli.yamls

    tester_file_name = 'lookup_%s_style_recursive.yml' % lookup_style
    tester_file = os.path.join(utils.TESTS_CWD, tester_file_name)

    # load settings from yaml and set them into Lookup 'settings' class var
    cli.yamls.Lookup.settings = configure.Configuration().from_file(
        tester_file).configure()
    # cli.yamls.Lookup.handling_nested_lookups = False

    if lookup_style == 'new':
        # explicitly call 'in_string_lookup' in order to create Lookup objects
        cli.yamls.Lookup.in_string_lookup()

    # dump the settings in order to retrieve the key's value and load them
    # again for value validation
    settings = yaml.safe_load(
        yaml.safe_dump(cli.yamls.Lookup.settings, default_flow_style=False))

    assert settings['foo']['test1'] == "key was found"
    assert settings['foo']['test2'] == "key was found"
