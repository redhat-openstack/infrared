from infrared.core.utils.exceptions import IRValidatorException
from ConfigParser import RawConfigParser

import jsonschema
import yaml
import os


class Validator(object):

    @classmethod
    def validate_from_file(cls, yaml_file=None):
        """
        Loads & validates that a YAML file has all required fields
        :param yaml_file: Path to YAML file
        :raise IRValidatorException: when mandatory data is missing in file
        :return: Dictionary with data loaded from a YAML file
        """
        if yaml_file is None:
            raise IRValidatorException(
                "YAML file is missing")

        if not os.path.isfile(yaml_file):
            raise IRValidatorException(
                "The YAML file doesn't exist: {}".format(yaml_file))

        with open(yaml_file) as fp:
            spec_dict = cls.validate_from_content(fp.read())

        return spec_dict

    @classmethod
    def validate_from_content(cls, file_content=None):
        """
        validates that YAML content has all required fields
        :param file_content: content of the YAML file
        :raise IRValidatorException: when mandatory data is missing in file
        :return: Dictionary with data loaded from a YAML file
        """
        raise NotImplementedError


class SpecValidator(Validator):
    """
    Class for validating that a plugin spec (YAML) has all required fields
    """
    CONFIG_PART_SCHEMA = {
        "type": "object",
        "properties": {
            "plugin_type": {"type": "string", "minLength": 1},
            "entry_point": {"type": "string", "minLength": 1},
        },
        "additionalProperties": False,
        "required": ["plugin_type"]
    }

    SUBPARSER_PART_SCHEMA = {
        "type": "object",
        "minProperties": 1,
        "maxProperties": 1,
        "patternProperties": {
            "^(?!(?:all)$).+$": {
                "type": "object",
            }
        },
        "additionalProperties": False
    }

    SCHEMA_WITH_CONFIG = {
        "type": "object",
        "properties": {
            "description": {"type": "string", "minLength": 1},
            "config": CONFIG_PART_SCHEMA,
            "subparsers": SUBPARSER_PART_SCHEMA
        },
        "additionalProperties": False,
        "required": ["config", "subparsers"]
    }

    SCHEMA_WITHOUT_CONFIG = {
        "type": "object",
        "properties": {
            "plugin_type": {"type": "string", "minLength": 1},
            "entry_point": {"type": "string", "minLength": 1},
            "description": {"type": "string", "minLength": 1},
            "subparsers": SUBPARSER_PART_SCHEMA
        },
        "additionalProperties": False,
        "required": ["plugin_type", "subparsers"]
    }

    @classmethod
    def validate_from_content(cls, spec_content=None):
        """validates that spec (YAML) content has all required fields

        :param spec_content: content of spec file
        :raise IRValidatorException: when mandatory data
        is missing in spec file
        :return: Dictionary with data loaded from a spec (YAML) file
        """
        if spec_content is None:
            raise IRValidatorException(
                "Plugin spec content is missing")

        spec_dict = yaml.load(spec_content)

        if not isinstance(spec_dict, dict):
            raise IRValidatorException(
                "Spec file is empty or corrupted: {}".format(spec_content))

        # check if new spec file structure
        try:
            if "config" in spec_dict:
                jsonschema.validate(spec_dict,
                                    cls.SCHEMA_WITH_CONFIG)
            else:
                jsonschema.validate(spec_dict,
                                    cls.SCHEMA_WITHOUT_CONFIG)

        except jsonschema.exceptions.ValidationError as error:
            raise IRValidatorException(
                "{} in file:\n{}".format(error.message, spec_content))

        subparsers_key = "subparsers"
        if "description" not in spec_dict \
                and "description" not in spec_dict[subparsers_key].values()[0]:
            raise IRValidatorException(
                "Required key 'description' is missing for supbarser '{}' in "
                "spec file: {}".format(
                    spec_dict[subparsers_key].keys()[0], spec_content))

        return spec_dict


class RegistryValidator(Validator):
    SCHEMA_REGISTRY = {
        "type": "object",
        "patternProperties": {
            "^.+$": {
                "type": "object",
                "properties": {
                    "src": {"type": "string", "minLength": 1},
                    "src_path": {"type": "string", "minLength": 1},
                    "rev": {"type": "string", "minLength": 1},
                    "desc": {"type": "string", "minLength": 1},
                    "type": {"type": "string", "minLength": 1},
                },
                "additionalProperties": False,
                "required": ["src", "desc", "type"]
            }
        },
        "additionalProperties": False,
    }

    @classmethod
    def validate_from_content(cls, file_content=None):
        """
        validates that Registry YAML content has all required fields
        :param file_content: content of the Registry YAML file
        :raise IRValidatorException: when mandatory data is missing in Registry
        :return: Dictionary with data loaded from a Registry YAML file
        """
        if file_content is None:
            raise IRValidatorException(
                "Registry YAML content is missing")

        registry_dict = yaml.load(file_content)

        if not isinstance(registry_dict, dict):
            raise IRValidatorException(
                "Registry file is empty or corrupted: {}".format(file_content))

        try:
            # validate schema
            jsonschema.validate(registry_dict,
                                cls.SCHEMA_REGISTRY)

        except jsonschema.exceptions.ValidationError as error:
            raise IRValidatorException(
                "{} in file:\n{}".format(error.message, file_content))

        return registry_dict


class AnsibleConfigValidator(Validator):
    IR_DOC_URL = 'http://infrared.readthedocs.io/en/stable/setup.html#' \
                 'ansible-configuration'

    SCHEMA_ANSIBLE_DEFAULT_OPTIONS = {
        "type": "object",
        "properties": {
            "host_key_checking": {"type": "string", "pattern": "^(F|f)alse$"},
            "forks": {"type": "integer", "minimum": 500},
            "timeout": {"type": "integer", "minimum": 30}
        },
        "additionalProperties": True,
        "required": ["host_key_checking", "forks", "timeout"]
    }

    SCHEMA_ANSIBLE_CONFIG = {
        "type": "object",
        "properties": {
            "defaults": SCHEMA_ANSIBLE_DEFAULT_OPTIONS
        },
        "additionalProperties": True,
        "required": ["defaults"]
    }

    @classmethod
    def validate_from_file(cls, yaml_file=None):
        config = RawConfigParser()
        config.read(yaml_file)
        config_json = cls._convert_config_to_dict(config)

        try:
            # validate schema
            jsonschema.validate(config_json,
                                cls.SCHEMA_ANSIBLE_CONFIG)

        except jsonschema.exceptions.ValidationError:
            raise IRValidatorException(
                "There is an issue with Ansible configuration in {}, "
                "for more info please check at {}\n"
                "Mandatory config options:\n"
                "- 'host_key_checking' to be False\n"
                "- 'forks' greater than 500\n"
                "- 'timeout' greater than 30\n".format(yaml_file,
                                                       cls.IR_DOC_URL))

    @classmethod
    def validate_from_content(cls, file_content=None):
        pass

    @staticmethod
    def _convert_config_to_dict(config):
        config_dict = {}
        for section in config.sections():
            if section not in config_dict:
                config_dict[section] = {}

            for option in config.options(section):
                option_value = config.get(section, option)
                try:
                    option_value = int(option_value)
                except ValueError:
                    pass

                config_dict[section][option] = option_value

        return config_dict
