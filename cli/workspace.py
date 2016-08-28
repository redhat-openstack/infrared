import datetime
import time

import os
from cli import exceptions

TIME_FORMAT = '%Y-%m-%d_%H-%M-%S'


class Workspace(object):
    def __init__(self, path):
        self.name = os.path.basename(path)
        self.path = path


class WorkspaceManager(object):
    workspacedir = os.path.join(os.path.expanduser("~"), ".infrared",
                                "workspaces")

    @classmethod
    def create(cls, name=""):
        name = name or "workspace_" + datetime.datetime.fromtimestamp(
            time.time()).strftime(TIME_FORMAT)
        path = os.path.join(WorkspaceManager.workspacedir, name)
        if os.path.exists(path):
            raise exceptions.IRWorspaceExists(workspace=name)
        os.makedirs(path)
        return Workspace(path=path)

    @classmethod
    def list(cls):
        # walk returns the basedir as well. need to remove it
        dirlist = [os.path.basename(d[0]) for d in os.walk(
            cls.workspacedir)][1:]
        return dirlist

    @classmethod
    def get(cls, name):
        path = os.path.join(WorkspaceManager.workspacedir, name)
        if os.path.exists(path):
            return Workspace(path)
        else:
            raise exceptions.IRWorspaceMissing(workspace=name)
