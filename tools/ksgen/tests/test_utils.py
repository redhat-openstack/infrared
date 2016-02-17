import logging
from ksgen import yaml_utils
from os.path import dirname, realpath

TEST_DIR = dirname(realpath(__file__))
yaml_utils.register()


def print_yaml(msg, x):
    logging.info(yaml_utils.to_yaml(msg, x))


def verify_key_val(cfg, source_dict, key):
    """ Assuming cfg is created from source_dict, returns true if
    cfg[key] == source_dict[key]"""

    keys = key.split('.')

    leaf_cfg = cfg
    leaf_dict = source_dict
    for k in keys:
        leaf_cfg = leaf_cfg[k]
        leaf_dict = leaf_dict[k]
    return leaf_cfg == leaf_dict


def _enable_logging(level=None):
    level = level or "debug"

    from ksgen import log_color
    log_color.enable()

    numeric_val = getattr(logging, level.upper(), None)
    if not isinstance(numeric_val, int):
        raise ValueError("Invalid log level: %s" % level)
    fmt = "%(filename)15s:%(lineno)3s| %(funcName)20s() : %(message)s"
    logging.basicConfig(level=numeric_val, format=fmt)


def usage(namespace):
    doc_string = """
    %(usage)s

Methods:
    %(methods)s
    """ % {
        "usage": namespace.get('__doc__'),
        "methods": '\n    '.join([
            m for m in namespace.keys() if m.startswith('test_')
        ])
    }
    print doc_string


def main(namespace):
    import sys
    _enable_logging()
    try:
        fn = sys.argv[1]
    except IndexError:
        sys.exit(usage(namespace))

    if fn not in namespace:
        sys.exit(usage(namespace))
    ret = namespace[fn]()
    sys.exit(ret)
