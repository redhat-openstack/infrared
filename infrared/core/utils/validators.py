from infrared.core.utils.exceptions import IRValidatorException
from infrared.core.utils.logger import LOG as logger
from six.moves import configparser

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

        spec_dict = yaml.safe_load(spec_content)

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
        if ("description" not in spec_dict and "description"
                not in list(spec_dict[subparsers_key].values())[0]):
            raise IRValidatorException(
                "Required key 'description' is missing for supbarser '{}' in "
                "spec file: {}".format(
                    list(spec_dict[subparsers_key].keys())[0], spec_content))

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
    ANSIBLE_CONFIG_OPTIONS = {
        'defaults': {
            'host_key_checking': {
                'type': 'bool',
                'comparison': 'eq',
                'expected_value': False,
                'critical': True
            },
            'forks': {
                'type': 'int',
                'comparison': 'gt',
                'expected_value': 500,
                'critical': False
            },
            'timeout': {
                'type': 'int',
                'comparison': 'gt',
                'expected_value': 30,
                'critical': False
            }
        }
    }

    @classmethod
    def validate_from_file(cls, yaml_file=None):
        config = configparser.RawConfigParser()
        config.read(yaml_file)
        config_dict = cls._convert_config_to_dict(config)

        for section, option_details in cls.ANSIBLE_CONFIG_OPTIONS.items():
            for opt_name, opt_params in option_details.items():
                try:
                    config_value = config_dict[section][opt_name]
                    cls._validate_config_option(yaml_file,
                                                opt_name,
                                                opt_params['type'],
                                                opt_params['comparison'],
                                                opt_params['expected_value'],
                                                config_value,
                                                opt_params['critical'])
                except KeyError:
                    cls._handle_missing_value(yaml_file, section, opt_name,
                                              opt_params['expected_value'],
                                              opt_params['critical'])

    @classmethod
    def validate_from_content(cls, file_content=None):
        pass

    @classmethod
    def _validate_config_option(cls, yaml_file, opt_name, opt_type,
                                comparison, exp_value, cur_value, critical):
        if opt_type == 'int':
            cur_value = int(cur_value)
        if opt_type == 'bool':
            if cur_value == 'True':
                cur_value = True
            else:
                cur_value = False

        if comparison == 'eq':
            if cur_value != exp_value:
                cls._handle_wrong_value(yaml_file, opt_name, exp_value,
                                        cur_value, critical)

        if comparison == 'gt':
            if cur_value < exp_value:
                cls._handle_wrong_value(yaml_file, opt_name, exp_value,
                                        cur_value, critical)

    @classmethod
    def _handle_wrong_value(cls, yaml_file, option_name, exp_value,
                            cur_value, critical):
        msg = "There is an issue with Ansible configuration in " \
              "{}. Expected value for the option '{}' is '{}', " \
              "current value is '{}'".format(yaml_file, option_name,
                                             exp_value, cur_value)
        if critical:
            raise IRValidatorException(msg)
        else:
            logger.warn(msg)

    @classmethod
    def _handle_missing_value(cls, yaml_file, section, option_name,
                              exp_value, critical):
        msg = "There is an issue with Ansible configuration in" \
              " {}. Option '{}' with value of '{}' not found in" \
              " section '{}'".format(yaml_file, option_name,
                                     exp_value, section)
        if critical:
            raise IRValidatorException(msg)
        else:
            logger.warn(msg)

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
