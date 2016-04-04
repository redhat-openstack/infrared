import os.path

import configure
import pytest
import yaml
from cli import exceptions

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

    assert settings['place']['holder']['validator'] == \
        "'!placeholder' has been overwritten"
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


def test_circular_reference_lookup():
    import cli.yamls

    tester_file_name = 'lookup_new_style_circular_reference.yml'
    tester_file = os.path.join(utils.TESTS_CWD, tester_file_name)

    # load settings from yaml and set them into Lookup 'settings' class var
    cli.yamls.Lookup.settings = configure.Configuration().from_file(
        tester_file).configure()
    # cli.yamls.Lookup.handling_nested_lookups = False
    cli.yamls.Lookup.in_string_lookup()

    # dump the settings in order to retrieve the key's value and load them
    # again for value validation

    with pytest.raises(exceptions.IRInfiniteLookupException):
        yaml.safe_load(
            yaml.safe_dump(cli.yamls.Lookup.settings,
                           default_flow_style=False))


def test_yamls_load(tmpdir):
    """
    Verify yamls module can load yaml file properly.
    """
    import cli.yamls

    p = tmpdir.mkdir("yamls").join("test_load.yml")
    p.write("""---
network:
    ip: 0.0.0.0
    mask: 255.255.255.255

intkey: 1
strkey: Value2
""")

    res = cli.yamls.load(p.strpath)

    assert isinstance(res, dict)
    assert 'network' in res
    assert 'ip' in res['network']
    assert res['network']['ip'] == '0.0.0.0'
    assert 'mask' in res['network']
    assert res['network']['mask'] == '255.255.255.255'
    assert 'intkey' in res
    assert res['intkey'] == 1
    assert 'strkey' in res
    assert res['strkey'] == "Value2"


@pytest.mark.parametrize("random_arg", [0, 1, 5, 10])
def test_yamls_random(tmpdir, random_arg):
    """
    Verifies the random constructor for yaml files.
    """
    import cli.yamls

    p = tmpdir.mkdir("yamls").join("test_yamls_random.yml")
    p.write("""---
random_string: !random {}
    """.format(random_arg))

    res = cli.yamls.load(p.strpath)
    assert 'random_string' in res
    assert len(res['random_string']) == random_arg
