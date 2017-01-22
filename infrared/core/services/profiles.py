import datetime
import os
import shutil
import tarfile
import time

from ansible.parsing.dataloader import DataLoader
from ansible import inventory
from ansible.vars import VariableManager

from infrared.core.utils import exceptions, logger
LOG = logger.LOG

TIME_FORMAT = '%Y-%m-%d_%H-%M-%S'

INVENTORY_LINK = "hosts"
LOCAL_HOSTS = """[local]
localhost ansible_connection=local ansible_python_interpreter=python
"""


class ProfileRegistry(object):
    """Profile registry holds the profile variable data

    Registry data needs to be cleaned up prior plugin execution
    and then link folder again from the used profile.
    """

    REGISTRY_FILE_NAME = ".registry"

    def __init__(self, path):
        self.path = path
        self.registry_file = os.path.join(path, self.REGISTRY_FILE_NAME)

        # create file if not present
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

    @property
    def inventory(self):
        """Profile inventory file.

        Creates the default inventory file in the profile dir if missing.

        The inventory file is the profile's "source of truth".
        * It tells ansibe where the profile is ({{ inventory_dir}})
        * It tells InfraRed the profile node list.
        * It holds node attributes and ssh tunneling if required

        Over time, multiple files might be created in the directory. The active
        one is always the target of INVENTORY_LINK symlink.
        """

        if not getattr(self, '_inventory', None):
            self._inventory = os.path.join(self.path, INVENTORY_LINK)
            if not os.path.exists(self._inventory):
                with open(os.path.join(self.path, 'local_hosts'),
                          'w') as stream:
                    stream.write(LOCAL_HOSTS)
                # create a 'hosts' link
                self.link_file(stream.name, dest_name=self._inventory,
                               add_to_reg=False)
        return self._inventory

    @inventory.setter
    def inventory(self, filename):
        """Updates profiles inventory

        Copy filename into profile dir.
        Update inventory symnlink to point to new local file.

        :param filename: new inventory file
        """
        new_inventory = self.copy_file(file_path=filename)
        self._inventory = os.path.join(self.path, INVENTORY_LINK)
        self.link_file(new_inventory, dest_name=self._inventory,
                       add_to_reg=False)

    def clear_links(self):
        """Clears all the created links."""

        first = self.registy.pop()
        while first is not None:
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

        # NOTE(oanufrii): Make file_path relative if it in self.path
        file_path = file_path.replace(self.path, ".")

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
                if not (os.path.exists(target_path) and
                        os.path.samefile(abs_path, target_path)):
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
    playbooks executions. Additionally all the generated files
    will go to the profile folder.

    At least one profile will be active.
    """

    def __init__(self, profiles_base_dir):
        self.profile_dir = profiles_base_dir

        if not os.path.isdir(self.profile_dir):
            os.makedirs(self.profile_dir)

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
        """Lists all the existing profiles.

        walk returns the basedir as well. need to remove it and avoid listing
        subfolders
        """
        dirlist = list(os.walk(self.profile_dir))
        if dirlist:
            return [Profile(os.path.basename(d),
                            os.path.join(self.profile_dir, d))
                    for d in dirlist[0][1]]
        else:
            return []

    def get(self, name):
        """Gets an exisiting profile."""

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

    def export_profile(self, profile_name, file_name=None):
        """Export content of profile folder as gzipped tar file

           Replaces existing .tgz file
        """

        if profile_name:
            profile = self.get(profile_name)
            if profile is None:
                raise exceptions.IRProfileMissing(profile=profile_name)
        else:
            profile = self.get_active_profile()
            if profile is None:
                raise exceptions.IRNoActiveProfileFound()

        fname = file_name or profile.name

        with tarfile.open(fname + '.tgz', "w:gz") as tar:
            tar.add(profile.path, arcname="./")

        print("Profile {} is exported to file {}.tgz".format(profile.name,
                                                             fname))

    def import_profile(self, file_name, profile_name=None):
        """Import profile from gzipped tar file

           Profile name should be unique
        """

        if not os.path.exists(file_name):
            raise IOError("File {} not found.".format(file_name))
        if profile_name is None:
            basename = os.path.basename(file_name)
            profile_name = ".".join(basename.split(".")[:-1])

        new_profile = self.create(name=profile_name)

        LOG.debug("Importing profile from file {} to path {}".format(
            file_name, new_profile.path))
        with tarfile.open(file_name) as tar:
            tar.extractall(path=new_profile.path)

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

    def node_list(self, profile_name=None):
        """Lists nodes and connection types from profile's inventory

           nodes with connection type 'local' are skipped
           :param profile_name: profile name to list nodes from.
                                Use active profile as default
        """

        profile = self.get(
            profile_name) if profile_name else self.get_active_profile()

        if profile is None:
            if profile_name is None:
                raise exceptions.IRNoActiveProfileFound()
            else:
                raise exceptions.IRProfileMissing(profile=profile_name)

        invent = inventory.Inventory(DataLoader(), VariableManager(),
                                     host_list=profile.inventory)
        hosts = invent.get_hosts()
        return [(host.name, host.address) for host in hosts if host.vars.get(
            "ansible_connection") != "local"]
