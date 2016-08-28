import datetime
import time
import os
import shutil

from cli import exceptions
from cli import logger

LOG = logger.LOG

TIME_FORMAT = '%Y-%m-%d_%H-%M-%S'

LOCAL_HOSTS = """[local]
localhost ansible_connection=local ansible_python_interpreter=python
"""


class Workspace(object):
    INVENTORY_FILES = ["hosts", "inventory"]

    def __init__(self, path, inventory=None):
        self.name = os.path.basename(path)
        self.path = path
        self.inventory = inventory

    def _filename(self, filename):
        """Helper function. construct path without validation"""
        return os.path.join(self.path, filename)

    def get(self, filename):
        """get a path to file in workspace"""
        path = self._filename(filename)
        if os.path.exists(path):
            return path
        raise exceptions.IRWorkspaceMissingFile(workspace=self.name,
                                                filename=filename)

    # todo(yfried): consider using Ansible inventory object
    @property
    def inventory(self):
        return self._inventory

    @inventory.setter
    def inventory(self, path):
        """Set inventory file.

        if provided, copy file into workspace as "inventory"

        else, search workspace for files generated by infrared (will have
        "hosts" as symlink to file)

        If not file, write LOCAL_HOST template to workspace
        """
        _symlink = "hosts"
        if path:
            LOG.debug("Import inventory file {}".format(path))
            shutil.copy2(path, self.path)
            self._inventory = self.get(os.path.basename(path))
            # self._inventory = self._filename("inventory")
            # shutil.copyfile(path, self._inventory)
        else:
            try:
                self._inventory = self.get(_symlink)
                LOG.debug("Found inventory file {} in workspace".format(
                    self._inventory))
                return
            except exceptions.IRWorkspaceMissingFile:
                LOG.debug("Create default inventory")
                self._inventory = self._filename("local_host")
                with open(self._inventory, 'w') as f:
                    f.write(LOCAL_HOSTS)
        os.symlink(self._inventory, self._filename(_symlink))



class WorkspaceManager(object):
    # todo(yfried): move to conf
    workspacedir = os.path.join(os.path.expanduser("~"), ".infrared",
                                "workspaces")

    @classmethod
    def create(cls, name="", *args, **kwargs):
        """Create a new workspace."""
        name = name or "workspace_" + datetime.datetime.fromtimestamp(
            time.time()).strftime(TIME_FORMAT)
        path = os.path.join(WorkspaceManager.workspacedir, name)
        if os.path.exists(path):
            raise exceptions.IRWorkspaceExists(workspace=name)
        os.makedirs(path)
        LOG.debug("Workspace {} created in {}".format(name, path))
        return Workspace(path=path, *args, **kwargs)

    @classmethod
    def list(cls):
        """list existing workspaces."""
        # walk returns the basedir as well. need to remove it
        dirlist = [os.path.basename(d[0]) for d in os.walk(
            cls.workspacedir)][1:]
        return dirlist

    @classmethod
    def use(cls, name, *args, **kwargs):
        """Use an existing workspace."""
        path = os.path.join(WorkspaceManager.workspacedir, name)
        if os.path.exists(path):
            LOG.debug("Reusing workspace {} in {}".format(name, path))
            return Workspace(path, *args, **kwargs)
        else:
            raise exceptions.IRWorkspaceMissing(workspace=name)

    @classmethod
    def get(cls, name, *args, **kwargs  ):
        """Get a workspace. Create new one if one doesn't exist."""

        try:
            return cls.create(name=name, *args, **kwargs)
        except exceptions.IRWorkspaceExists:
            return cls.use(name=name, *args, **kwargs)
