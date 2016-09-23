import os.path

import pytest
import yaml

from tests.test_cwd import utils as test_utils
from infrared.core.utils import yamls
from infrared.core.utils import utils as core_utils
from infrared.core.utils import exceptions

our_cwd_setup = test_utils.our_cwd_setup

def test_unsupported_yaml_constructor(our_cwd_setup):
    tester_file = 'IRYAMLConstructorError.yml'
    with pytest.raises(exceptions.IRYAMLConstructorError):
        yamls.load(os.path.join(test_utils.TESTS_CWD, tester_file))


def test_placeholder_validator(our_cwd_setup):

    injector = 'placeholder_injector.yml'
    overwriter = 'placeholder_overwriter.yml'

    # Checks that 'IRPlaceholderException' is raised if value isn't been
    # overwritten
    settings = yamls.load(os.path.join(test_utils.TESTS_CWD, injector))
    assert isinstance(settings['place']['holder']['validator'], yamls.Placeholder)
    with pytest.raises(exceptions.IRPlaceholderException) as exc:
        yaml.safe_dump(settings, default_flow_style=False)
    assert "Mandatory value is missing." in str(exc.value.message)

    # Checks that exceptions haven't been raised after overwriting the
    # placeholder
    overwriter_dict = yamls.load(os.path.join(test_utils.TESTS_CWD, overwriter))
    core_utils.dict_merge(settings, overwriter_dict)
    assert settings['place']['holder']['validator'] == \
        "'!placeholder' has been overwritten"
    yaml.safe_dump(settings, default_flow_style=False)


def test_placeholder_double_validator(our_cwd_setup):
    injector = 'placeholder_double_injector.yml'

    # Checks that 'IRPlaceholderException' is raised if value isn't been
    # overwritten
    settings = yamls.load(os.path.join(test_utils.TESTS_CWD, injector))

    assert isinstance(settings['place']['holder']['validator1'], yamls.Placeholder)
    assert isinstance(settings['place']['holder']['validator2'], yamls.Placeholder)
    with pytest.raises(exceptions.IRPlaceholderException) as exc:
        yaml.safe_dump(settings, default_flow_style=False)
    assert "Mandatory value is missing." in str(exc.value.message)


def test_lookup_basic(our_cwd_setup):

    tester_file_name = 'lookup_basic.yml'
    tester_file_path = os.path.join(test_utils.TESTS_CWD, tester_file_name)

    with open(tester_file_path) as fp:
        settings = yaml.load(fp)
        yamls.replace_lookup(settings)

    assert settings['foo']['key_to_be_found'] == "key was found"


def test_lookup_non_existing_key(our_cwd_setup):
    tester_file_name = 'lookup_non_existing_key.yml'
    tester_file_path = os.path.join(test_utils.TESTS_CWD, tester_file_name)

    with open(tester_file_path) as fp:
        settings = yaml.load(fp)

    with pytest.raises(exceptions.IRKeyNotFoundException):
        yamls.replace_lookup(settings)


def test_nested_lookup(our_cwd_setup):
    tester_file_name = 'lookup_nested.yml'
    tester_file_path = os.path.join(test_utils.TESTS_CWD, tester_file_name)

    with open(tester_file_path) as fp:
        settings = yaml.load(fp)
        yamls.replace_lookup(settings)

    assert settings['foo']['test1'] == "key was found"


def test_recursive_lookup(our_cwd_setup):
    tester_file_name = 'lookup_recursive.yml'
    tester_file_path = os.path.join(test_utils.TESTS_CWD, tester_file_name)

    with open(tester_file_path) as fp:
        settings = yaml.load(fp)
        yamls.replace_lookup(settings)

    assert settings['foo']['test1'] == "key was found"
    assert settings['foo']['test2'] == "key was found"


def test_in_list_lookup(our_cwd_setup):
    tester_file_name = 'lookup_in_list.yml'
    tester_file_path = os.path.join(test_utils.TESTS_CWD, tester_file_name)

    with open(tester_file_path) as fp:
        yaml_content = yaml.load(fp)
        yamls.replace_lookup(yaml_content)

    assert yaml_content['key1']['key12'] == ["pre", "found", "post"]


def test_integer_key_conversion_in_lookup(our_cwd_setup):
    """
    Makes sure that integer keys remain integer after lookup method
    """
    tester_file_name = 'lookup_int_key_conversion.yml'
    tester_file_path = os.path.join(test_utils.TESTS_CWD, tester_file_name)

    with open(tester_file_path) as fp:
        yaml_content = yaml.load(fp)
        yamls.replace_lookup(yaml_content)

    assert yaml_content['key'][1] == 'val'
    with pytest.raises(KeyError):
        yaml_content['key']['1'] == 'val'


def test_same_key_multiple_visits_lookup(our_cwd_setup):
    """
    Checks that key's path is removed from the 'visited' list when each
    lookup is found
    """
    tester_file_name = 'lookup_same_key_multiple_visits.yml'
    tester_file_path = os.path.join(test_utils.TESTS_CWD, tester_file_name)

    with open(tester_file_path) as fp:
        yaml_content = yaml.load(fp)
        yamls.replace_lookup(yaml_content)

    assert yaml_content['key']['sub2'] == 'val-val'


def test_circular_reference_lookup():
    tester_file_name = 'lookup_new_style_circular_reference.yml'
    tester_file_path = os.path.join(test_utils.TESTS_CWD, tester_file_name)

    with open(tester_file_path) as fp:
        settings = yaml.load(fp)

    with pytest.raises(exceptions.IRInfiniteLookupException):
        yamls.replace_lookup(settings)


def test_yamls_load(tmpdir):
    """
    Verify yamls module can load yaml file properly.
    """
    p = tmpdir.mkdir("yamls").join("test_load.yml")
    p.write("""---
network:
    ip: 0.0.0.0
    mask: 255.255.255.255

intkey: 1
strkey: Value2
""")

    res = yamls.load(p.strpath)

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
    p = tmpdir.mkdir("yamls").join("test_yamls_random.yml")
    p.write("""---
random_string: !random {}
    """.format(random_arg))

    res = yamls.load(p.strpath)
    assert 'random_string' in res
    assert len(res['random_string']) == random_arg
