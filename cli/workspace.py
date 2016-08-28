import datetime
import time
import os
import shutil

from cli import exceptions
from cli import logger

LOG = logger.LOG

TIME_FORMAT = '%Y-%m-%d_%H-%M-%S'


class Workspace(object):
    def __init__(self, path, inventory=""):
        self.name = os.path.basename(path)
        self.path = path
        self._inventory = inventory

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

    @property
    def inventory(self):
        return self._inventory

    @inventory.setter
    def inventory(self, path):
        if path:
            shutil.copyfile(path, self._filename("inventory"))


class WorkspaceManager(object):
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
    def get(cls, name, *args, **kwargs):
        """Get a workspace. Create new one if one doesn't exist."""

        try:
            return cls.create(name=name, *args, **kwargs)
        except exceptions.IRWorkspaceExists:
            return cls.use(name=name, *args, **kwargs)
