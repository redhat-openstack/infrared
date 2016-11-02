import datetime
import os
import shutil
import time

from infrared.core.utils import exceptions, logger

LOG = logger.LOG

TIME_FORMAT = '%Y-%m-%d_%H-%M-%S'

LOCAL_HOSTS = """[local]
localhost ansible_connection=local ansible_python_interpreter=python
"""

class ProfileRegistry(object):
    """Profile resitry holds the profile variable data

    Registry data needs to be cleaned up prior plugin execution
    and then link folder agains from the used profile.
    """

    REGISTRY_FILE_NAME = ".registry"

    def __init__(self, path):
        self.path = path
        self.registry_file = os.path.join(path, self.REGISTRY_FILE_NAME)

        # creat file if not present
        if not os.path.exists(self.registry_file):
            open(self.registry_file, 'a').close()

    def put(self, file_name):
        """Puts the file in to the registry."""

        with open(self.registry_file, 'a+') as stream:
            stream.write(file_name + '\n')

    def pop(self):
        """Pops the file from registry."""

        with open(self.registry_file) as stream:
            lines = stream.readlines()

        with open(self.registry_file, 'w') as stream:
            stream.writelines(lines[1:])

        return lines[0].rstrip('\n') if lines else None


class Profile(object):
    """Holds the information about a profile."""

    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.registy = ProfileRegistry(self.path)

    def create_default_inventory(self, name):
        """Creates the deafault inventory file in the profile dir.

        Creates also the hosts symlink which points the default inventory file.
        """

        abs_path = os.path.join(self.path, name)
        with open(abs_path, 'w') as stream:
            stream.write(LOCAL_HOSTS)

        # create a 'hosts' link
        self.link_file(abs_path, dest_name='hosts', add_to_reg=False)

    def clear_links(self):
        """Clears all the created links."""

        first = self.registy.pop()
        while first != None:
            if os.path.islink(first):
                LOG.debug("Removing link: %s", first)
                os.unlink(first)
            first = self.registy.pop()

    def link_file(self, file_path,
                  dest_name=None, unlink=True, add_to_reg=True):
        """Creates a link to a file within the profile folder.

        profile/filename -> file_path_on_system
        """
        if not dest_name:
            file_name = os.path.basename(os.path.normpath(file_path))
        else:
            file_name = dest_name

        target_path = os.path.join(self.path, file_name)

        if unlink and os.path.islink(target_path):
            os.unlink(target_path)

        LOG.debug("Creating link: src='%s', dest='%s'", file_path, target_path)
        os.symlink(file_path, target_path)
        if add_to_reg:
            self.registy.put(target_path)
        return target_path

    def copy_file(self, file_path, additional_lookup_dirs=None):
        """Copies specified file to the profile folder."""

        dirs = [os.path.curdir]
        if additional_lookup_dirs is not None:
            dirs.extend(additional_lookup_dirs)

        target_path = None
        for additional_dir in dirs:
            abs_path = os.path.join(additional_dir, file_path)
            if os.path.isfile(abs_path):
                target_path = os.path.join(
                    self.path,
                    os.path.basename(os.path.normpath(abs_path)))
                if not os.path.exists(target_path) or not os.path.samefile(abs_path, target_path):
                    LOG.debug("Copying file: src='%s', dest='%s'",
                              abs_path,
                              self.path)
                    shutil.copy2(abs_path, self.path)
                break
        if target_path is None:
            raise IOError("File not found: {}".format(file_path))
        return target_path


class ProfileManager(object):
    """Manages all the profiles.

    Profile is a folder which contains all the required file for
    palybooks executions. Additionaly all the generated files
    will go to the profile folder.

    At least one profile will be active.
    """

    def __init__(self, profiles_base_dir):
        self.profile_dir = profiles_base_dir
        self.active_file = os.path.join(self.profile_dir, ".active")

    def has_profile(self, name):
        """Checks if profile is present."""

        path = os.path.join(self.profile_dir, name)
        return os.path.exists(path)

    def create(self, name=None):
        """Creates a new profile.

        The default invnetory file (local_hosts) will be aslo created.
        """

        name = name or "profile_" + datetime.datetime.fromtimestamp(
            time.time()).strftime(TIME_FORMAT)
        path = os.path.join(self.profile_dir, name)
        if os.path.exists(path):
            raise exceptions.IRProfileExists(profile=name)
        os.makedirs(path)
        LOG.debug("Profile {} created in {}".format(name, path))
        profile = Profile(name, path)
        profile.create_default_inventory('local_hosts')
        return profile

    def activate(self, name):
        """Activates the profile."""

        if self.has_profile(name):
            with open(self.active_file, 'w') as prf_file:
                prf_file.write(name)
            LOG.debug("Activating profile %s in %s",
                      name,
                      os.path.join(self.profile_dir, name))
        else:
            raise exceptions.IRProfileMissing(profile=name)

    def delete(self, name):
        """Deactivate and removes the profile."""

        if not self.has_profile(name):
            raise exceptions.IRProfileMissing(profile=name)
        else:
            if self.is_active(name):
                os.remove(self.active_file)
            shutil.rmtree(os.path.join(self.profile_dir, name))

    def list(self):
        """Lists all the existing profiles."""

        # walk returns the basedir as well. need to remove it
        dirlist = [Profile(os.path.basename(d[0]), d[0]) for d in os.walk(
            self.profile_dir)][1:]
        return dirlist

    def get(self, name):
        """Gets the exisiting profile."""

        return next((profile for profile in self.list()
                     if profile.name == name), None)

    def get_active_profile(self):
        """Gets the active profile.

        If active profile is present then return the Profile object.
        Otherwise returns None
        """

        if os.path.isfile(self.active_file):
            with open(self.active_file) as prf_file:
                active_name = prf_file.read().strip()
                return self.get(active_name)

    def is_active(self, name):
        """Checks if profile is active."""

        active = self.get_active_profile()
        return False if active is None else active.name == name

    def cleanup(self, name):
        """Removes all the files from the profile folder"""

        was_active = self.is_active(name)
        self.delete(name)
        self.create(name)
        if was_active:
            self.activate(name)
