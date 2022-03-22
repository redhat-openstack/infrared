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


class IRConfigurationException(IRException):
    """General exception for any kind of configuration issues. """
    pass


class IRInfiniteLookupException(IRException):
    def __init__(self, value):
        message = "Lookup circular reference detected for: {}".format(value)
        super(IRInfiniteLookupException, self).__init__(message)


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


class IRInvalidChoiceException(IRException):
    def __init__(self, invalid_options):
        message = "The following arguments contain invalid choices:"
        for arg_name, arg_value, available_choices in invalid_options:
            message += \
                "\nArgument {}: invalid choice '{}' (choose from {})".format(
                    arg_name, arg_value, available_choices)
        super(self.__class__, self).__init__(message)


class IRInvalidLengthException(IRException):
    def __init__(self, invalid_options):
        message = "The following arguments contain invalid length:"
        for arg_name, arg_value, length in invalid_options:
            message += \
                "\nArgument {}: invalid length '{}' (should be " \
                "less or equal {})".format(arg_name,
                                           arg_value, length)
        super(self.__class__, self).__init__(message)


class IRInvalidMinMaxRangeException(IRException):
    def __init__(self, invalid_options):
        message = "The following arguments contain invalid options:"
        for name, expected_type, expected_value, value in invalid_options:
            message += "\nArgument {}: Expected {} should be {}, " \
                       "actual value is {}".format(name, expected_type,
                                                   expected_value, value)
        super(self.__class__, self).__init__(message)


class SpecParserException(Exception):
    """The spec parser specific exception.  """
    def __init__(self, message, errors):
        super(SpecParserException, self).__init__(message)
        self.errors = errors


# workspace exceptions
class IRWorkspaceExists(IRException):
    def __init__(self, workspace):
        message = "Workspace {} already exists".format(workspace)
        super(IRWorkspaceExists, self).__init__(message)


class IRWorkspaceMissing(IRException):
    def __init__(self, workspace):
        message = "Workspace {} doesn't exist".format(workspace)
        super(IRWorkspaceMissing, self).__init__(message)


class IRWorkspaceUndefined(IRConfigurationException):
    def __init__(self):
        message = "'workspaces' path undefined in 'infrared.cfg'. If you " \
                  "wish to use 'workspaces' feature, please define it. Use " \
                  "'infrared.cfg.example as template."
        super(IRWorkspaceUndefined, self).__init__(message)


class IRWorkspaceMissingFile(IRException):
    def __init__(self, workspace, filename):
        message = "File {} not found in Workspace {}".format(filename,
                                                             workspace)
        super(IRWorkspaceMissingFile, self).__init__(message)


class IRDefultWorkspaceException(IRException):
    def __init__(self):
        message = "Unable to remove or deactivate default workspace"
        super(IRDefultWorkspaceException, self).__init__(message)


class IRWorkspaceIsActive(IRException):
    def __init__(self, workspace):
        message = "Workspace is active: {}".format(workspace)
        super(IRWorkspaceIsActive, self).__init__(message)


class IRWorkspaceInvalidName(IRException):
    def __init__(self, workspace):
        message = "'{}' is not a valid name for workspace".format(workspace)
        super(IRWorkspaceInvalidName, self).__init__(message)


class IRWorkspaceActiveIsNotLink(IRException):
    def __init__(self, workspace_path):
        message = "Workspace path {} contains file or folder with name " \
                  "'active', expected is symlink".format(workspace_path)
        super(IRWorkspaceActiveIsNotLink, self).__init__(message)


class IRNoActiveWorkspaceFound(IRException):
    def __init__(self):
        message = "There is no active workspace found. " \
                  "You can create and checkout workspace by" \
                  " running the following command: " \
                  "\n infrared workspace checkout --create <workspace_name>"
        super(IRNoActiveWorkspaceFound, self).__init__(message)


class IRFailedToImportWorkspace(IRException):
    def __init__(self, reason):
        message = "Failed to import workspace: {}".format(reason)
        super(self.__class__, self).__init__(message)


class IRFailedToAddPlugin(IRException):
    def __init__(self, reason_str):
        super(self.__class__, self).__init__(reason_str)


class IRFailedToRemovePlugin(IRException):
    def __init__(self, reason_str):
        super(self.__class__, self).__init__(reason_str)


class IRUnsupportedPluginType(IRException):
    def __init__(self, plugin_type, additional_reason_str=None):
        reason_str = "'{}' plugin type isn't supported".format(plugin_type)

        if additional_reason_str is not None:
            reason_str += "\n" + additional_reason_str

        super(self.__class__, self).__init__(reason_str)


class IRFailedToUpdatePlugin(IRException):
    def __init__(self, reason_str):
        super(self.__class__, self).__init__(reason_str)


class IRFailedToImportPlugins(IRException):
    def __init__(self, reason):
        message = "Failed to import plugins: {}".format(reason)
        super(self.__class__, self).__init__(message)


class IRSshException(IRException):
    def __init__(self, msg):
        message = msg
        super(IRSshException, self).__init__(message)


class IRUnsupportedSpecOptionType(IRException):
    def __init__(self, message):
        super(self.__class__, self).__init__(message)


class IRKeyValueListException(IRException):
    def __init__(self, message):
        super(self.__class__, self).__init__(message)


class IRFileNotFoundException(IRException):
    def __init__(self, files):
        message = "Unable to find file in the following locations: {}".format(
            files)
        super(self.__class__, self).__init__(message)


class IRDeprecationException(IRException):
    def __init__(self, message):
        super(self.__class__, self).__init__(message)


class IRGroupNotFoundException(IRException):
    def __init__(self, group):
        message = "Unable to find group: {}".format(
            group)
        super(self.__class__, self).__init__(message)


class IRValidatorException(IRException):
    def __init__(self, reason_str):
        super(self.__class__, self).__init__(reason_str)


class IRPluginExistsException(IRException):
    def __init__(self, reason_str):
        super(self.__class__, self).__init__(reason_str)


class IRGalaxyRoleInstallFailedException(IRException):
    def __init__(self, reason_str):
        super(self.__class__, self).__init__(reason_str)


class IRExtraVarsException(IRException):
    def __init__(self, extra_var):
        super(self.__class__, self).__init__(
            '"%s" - extra-var argument must be in the "key=value" '
            'form' % extra_var)


class IRAnswersFileEnvVarNotDefined(IRException):
    def __init__(self, env_var):
        message = "Environment variable {} not defined".format(env_var)
        super(self.__class__, self).__init__(message)
