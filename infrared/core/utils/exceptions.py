class IRException(Exception):
    def __init__(self, message):
        self.message = message


class IRKeyNotFoundException(IRException):
    def __init__(self, key, dic):
        self.key = key
        self.dic = dic
        super(self.__class__, self).__init__(
            'Key "%s" not found in %s' % (key, dic))


class IRPrivateSettingsMissingException(IRException):
    def __init__(self, key):
        self.key = key
        super(self.__class__, self).__init__(
            "Settings key '{}' was not found. Check that you have "
            "your private settings referenced: "
            "add -e @<private settings file> to the invocation OR add "
            "the path the private settings folder in "
            "your infrared.cfg file.".format(key))


class IRFileNotFoundException(IRException):
    def __init__(self, file_path, msg=None):
        pre_msg = msg if msg else 'No such file(s) or directory(s): '
        super(self.__class__, self).__init__(pre_msg + str(file_path))


class IRExtraVarsException(IRException):
    def __init__(self, extra_var):
        super(self.__class__, self).__init__(
            '"%s" - extra-var argument must be a path to a setting file or '
            'in "key=value" form' % extra_var)


class IRMissingAncestorException(IRException):
    def __init__(self, key):
        super(self.__class__, self).__init__(
            'Please provide all ancestors of "--%s"' % key.replace("_", "-"))


class IRUndefinedEnvironmentVariableExcption(IRException):
    def __init__(self, env_var):
        super(self.__class__, self).__init__(
            'Environment variable "%s" is not defined' % env_var)


class IRYAMLConstructorError(IRException):
    def __init__(self, mark_obj, where):
        self.message = mark_obj.problem
        pm = mark_obj.problem_mark
        self.message += ' in:\n  "{where}", line {line_no}, column ' \
                        '{column_no}'.format(where=where,
                                             line_no=pm.line + 1,
                                             column_no=pm.column + 1)


class IRPlaceholderException(IRException):
    def __init__(self, trace_message):
        self.message = 'Mandatory value is missing.\n' + trace_message


class IRNotImplemented(IRException):
    pass


class IRUnknownSpecException(IRException):
    """
    This exceptions is raised when unknown application is
     started by user.
    """

    def __init__(self, app_name):
        self.app_name = app_name
        super(IRUnknownSpecException, self).__init__(
            "Spec is unknown: '{}'. Make sure the infrared configuration "
            "file has a section for that spec.".format(app_name))


class IRConfigurationException(IRException):
    """
    General exception for any kind of configuration issues.
    """
    pass


class IRInfiniteLookupException(IRException):
    def __init__(self, value):
        message = "Lookup circular reference detected for: {}".format(value)
        super(IRInfiniteLookupException, self).__init__(message)


class IREmptySettingsFile(IRException):
    def __init__(self, file_path):
        super(self.__class__, self).__init__("Empty settings files are not "
                                             "allowed: {}".format(file_path))


class IRWrongTopologyFormat(IRException):
    def __init__(self, used_format):
        message = \
            "Wrong topology nodes format has been given - '{}'\n" \
            "Topology format should be comma separated value in " \
            "<count_type> form.\n" \
            "Example:\n" \
            "  'controller:1,compute:2,undercloud:3'".format(used_format)
        super(self.__class__, self).__init__(message)


class IRWrongYamlListFormat(IRException):
    def __init__(self, used_format):
        message = \
            "Wrong yaml list format has been given - '{}'\n" \
            "Value should be comma separated string. " \
            "Example:\n" \
            "  'item1,item2,item3'".format(used_format)
        super(self.__class__, self).__init__(message)


class IRUnrecognizedOptionsException(IRException):
    def __init__(self, wrong_options):
        self.wrong_options = wrong_options
        message = \
            "The following options are not recognized:  '{}'".format(
                wrong_options)
        super(self.__class__, self).__init__(message)


class IRRequiredArgsMissingException(IRException):
    def __init__(self, missing_args):
        self.missing_args = missing_args

        message = 'Required options are not set:'
        for cmd_name, args in missing_args.items():
                message += ("\n * [{}]: {}".format(cmd_name, ", ".join(
                    ["'" + arg + "'" for arg in args])))
        super(IRRequiredArgsMissingException, self).__init__(message)


class SpecParserException(Exception):
    """
    The spec parser specific exception.
    """
    def __init__(self, message, errors):
        super(SpecParserException, self).__init__(message)
        self.errors = errors


# profile exceptions
class IRProfileExists(IRException):
    def __init__(self, profile):
        message = "Profile {} already exists".format(profile)
        super(IRProfileExists, self).__init__(message)


class IRProfileMissing(IRException):
    def __init__(self, profile):
        message = "Profile {} doesn't exist".format(profile)
        super(IRProfileMissing, self).__init__(message)


class IRProfileUndefined(IRConfigurationException):
    def __init__(self):
        message = "'profiles' path undefined in 'infrared.cfg'. If you wish " \
                  "to use 'profiles' feature, please define it. Use " \
                  "'infrared.cfg.example as template."
        super(IRProfileUndefined, self).__init__(message)


class IRProfileMissingFile(IRException):
    def __init__(self, profile, filename):
        message = "File {} not found in Profile {}".format(filename,
                                                           profile)
        super(IRProfileMissingFile, self).__init__(message)


class IRDefultProfileException(IRException):
    def __init__(self):
        message = "Unable to remove or deactivate default profile"
        super(IRDefultProfileException, self).__init__(message)


class IRProfileIsActive(IRException):
    def __init__(self, profile):
        message = "Profile is active: {}".format(profile)
        super(IRProfileIsActive, self).__init__(message)


class IRNoActiveProfileFound(IRException):
    def __init__(self):
        message = "There is no active profile found. " \
                  "You can create and activate profile by" \
                  " running the following commands: " \
                  "\n infrared profile create <profile_name>" \
                  "\n infrared profile activate <profile_name>"
        super(IRNoActiveProfileFound, self).__init__(message)
