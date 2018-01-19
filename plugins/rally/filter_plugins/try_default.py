from jinja2.runtime import Undefined
from jinja2.exceptions import UndefinedError

def try_default(value, default, ignore=False):
    """
    This filter ignores undefined variables and returns
    default value, if default value is undefined and 'ignore'
    options is enabled then return 'False' otherwise raise
    exception 'UndefinedError'.
    """

    if not isinstance(value, Undefined):
        return value
    elif not isinstance(default, Undefined):
        return default
    elif isinstance(default, Undefined) and ignore:
        return False
    else:
        raise UndefinedError("One of the nested variables are undefined")

class FilterModule(object):
    def filters(self):
        return {
            'try_default': try_default,
        }
