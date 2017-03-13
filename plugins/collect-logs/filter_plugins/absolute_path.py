import os


def absolute_path(target_path, rel_dir=None):
    """Returns an absolute path for a given target path

    If target_path is empty, rel_dir or cwd will be returned
    :param target_path: Target path to be "absolutized"
    :param rel_dir: A path to a base relative dir
    :return: (str) Absolute path of the given 'target_path'
    """
    dir_name = os.path.abspath(
        os.path.expanduser(rel_dir)) if rel_dir else os.getcwd()

    if not target_path:
        return dir_name

    target_path = os.path.expanduser(target_path)

    if os.path.isabs(target_path):
        return target_path

    return os.path.join(dir_name, target_path)


class FilterModule(object):
    def filters(self):
        return {
            'absolute_path': absolute_path,
        }
