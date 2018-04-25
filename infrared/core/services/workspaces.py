import datetime
import os
import fileinput
import shutil
import re
import tarfile
import tempfile
import time
import urllib2

from infrared.core.utils import exceptions, logger

LOG = logger.LOG

TIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
ACTIVE_WORKSPACE_ENV_NAME = "IR_WORKSPACE"

INVENTORY_LINK = "hosts"
LOCAL_HOSTS = """[local]
localhost ansible_connection=local ansible_python_interpreter=python
"""
EXCLUDED_GROUPS = ['all', 'local', 'ungrouped']


class WorkspaceRegistry(object):
    """Workspace registry holds the workspace variable data

    Registry data needs to be cleaned up prior plugin execution
    and then link folder again from the used workspace.
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


class Workspace(object):
    """Holds the information about a workspace."""

    path_placeholder = "%%workspace_dir%%"

    def __init__(self, name, path):
        self.name = name
        self.path = path
        self.registy = WorkspaceRegistry(self.path)

    @property
    def inventory(self):
        """Workspace inventory file.

        Creates the default inventory file in the workspace dir if missing.

        The inventory file is the workspace's "source of truth".
        * It tells ansibe where the workspace is ({{ inventory_dir}})
        * It tells infrared the workspace node list.
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
        """Updates workspaces inventory

        Copy filename into workspace dir.
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

    def _populate_paths(self):
        """Update inventory with new workspace directory path. """

        inv = self.inventory

        real_inv = os.path.join(os.path.dirname(inv), os.readlink(inv))

        for line in fileinput.input(real_inv, inplace=True):
            new_line = re.sub(self.path_placeholder, self.path,
                              line.rstrip())
            print new_line

    def _purge_paths(self, path):
        """replace path in inventory with placeholders.

        This method is used on tmp workspace, so we can't use self.path,
        we need original path.
        """
        inv = self.inventory

        real_inv = os.path.join(os.path.dirname(inv), os.readlink(inv))

        for line in fileinput.input(real_inv, inplace=True):
            new_line = re.sub(path,
                              self.path_placeholder,
                              line.rstrip())
            print new_line

    def _copy_outside_keys(self):
        """Copies SSH keys into the workspace's directory

        Also replaces workspace paths with workspace placeholder and updates
        the inventory file with the changes
        """
        real_inv = os.path.join(self.path, os.readlink(self.inventory))

        with open(real_inv, 'a+') as f:
            inventory_content = f.read()

            ssh_keys = set(re.findall(
                r"ansible_ssh_private_key_file=(\/\S+)", inventory_content))
            LOG.debug("SSH keys to copy:\n  {}".format(ssh_keys))

            for ssh_key in sorted(ssh_keys, reverse=True):
                # Skip SSH keys that already in the workspace
                if ssh_key.startswith(self.path) or \
                        ssh_key.startswith(self.path_placeholder):
                    continue

                ssh_key_name = os.path.basename(ssh_key)
                rand_str = next(tempfile._get_candidate_names())
                ssh_key_name_new = "{}-{}".format(ssh_key_name, rand_str)
                new_ssh_key = os.path.join(self.path, ssh_key_name_new)

                LOG.debug(
                    "Copying SSH key '{}' to workspace's dir: '{}'".format(
                        ssh_key, new_ssh_key))
                shutil.copy2(ssh_key, new_ssh_key)

                new_ssh_key_with_placeholder = \
                    os.path.join(self.path_placeholder, ssh_key_name_new)
                LOG.debug(
                    "Replacing SSH key '{}' path with workspace placeholder "
                    "'{}'".format(ssh_key, new_ssh_key_with_placeholder))
                inventory_content = re.sub(
                    ssh_key, new_ssh_key_with_placeholder, inventory_content)

            f.seek(0)
            f.truncate()
            f.write(inventory_content)

    def link_file(self, file_path,
                  dest_name=None, unlink=True, add_to_reg=True):
        """Creates a link to a file within the workspace folder.

        workspace/filename -> file_path_on_system
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
        """Copies specified file to the workspace folder."""

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


class WorkspaceManager(object):
    """Manages all the workspaces.

    Workspace is a folder which contains all the required file for
    playbooks executions. Additionally all the generated files
    will go to the workspace folder.

    At least one workspace will be active.
    """

    def __init__(self, workspaces_base_dir):
        self.workspace_dir = workspaces_base_dir

        if not os.path.isdir(self.workspace_dir):
            os.makedirs(self.workspace_dir)

        self.active_file = os.path.join(self.workspace_dir, ".active")

    def has_workspace(self, name):
        """Checks if workspace is present."""

        path = os.path.join(self.workspace_dir, name)
        return os.path.exists(path)

    def create(self, name=None):
        """Creates a new workspace.

        The default invnetory file (local_hosts) will be aslo created.
        """

        name = name or "workspace_" + datetime.datetime.fromtimestamp(
            time.time()).strftime(TIME_FORMAT)
        path = os.path.join(self.workspace_dir, name)
        if os.path.exists(path):
            raise exceptions.IRWorkspaceExists(workspace=name)
        os.makedirs(path)
        LOG.debug("Workspace {} created in {}".format(name, path))
        workspace = Workspace(name, path)
        return workspace

    def activate(self, name):
        """Activates the workspace.

        :param name: Name of the workspace to activate
        """

        if os.environ.get(ACTIVE_WORKSPACE_ENV_NAME):
            raise exceptions.IRException(
                message="'workspace checkout' command is disabled while "
                "{} environment variable is set.".format(
                    ACTIVE_WORKSPACE_ENV_NAME))

        if self.has_workspace(name):
            with open(self.active_file, 'w') as prf_file:
                prf_file.write(name)
            LOG.debug("Activating workspace %s in %s",
                      name,
                      os.path.join(self.workspace_dir, name))
        else:
            raise exceptions.IRWorkspaceMissing(workspace=name)

    def delete(self, name, keep_active_workspace_file=False):
        """Deactivates and removes the workspace.

        :param name: Name of the workspace to delete
        :param keep_active_workspace_file: Whether to keep the active
        workspace file or not (used in workspace cleanup)
        """

        if not self.has_workspace(name):
            raise exceptions.IRWorkspaceMissing(workspace=name)

        if os.path.isfile(self.active_file) and not keep_active_workspace_file:
            with open(self.active_file) as fp:
                f_active_workspace = fp.read().strip()
            if f_active_workspace == name:
                os.remove(self.active_file)

        shutil.rmtree(os.path.join(self.workspace_dir, name))

    def list(self):
        """Lists all the existing workspaces.

        walk returns the basedir as well. need to remove it and avoid listing
        subfolders
        """
        dirlist = list(os.walk(self.workspace_dir))
        if dirlist:
            return [Workspace(os.path.basename(d),
                              os.path.join(self.workspace_dir, d))
                    for d in dirlist[0][1]]
        else:
            return []

    def get(self, name):
        """Gets an existing workspace."""

        return next((workspace for workspace in self.list()
                     if workspace.name == name), None)

    def get_active_workspace(self):
        """Gets the active workspace.

        If active workspace is present then return the Workspace object.
        Otherwise returns None
        """
        active_name = os.environ.get(ACTIVE_WORKSPACE_ENV_NAME)

        if active_name is None:
            if os.path.isfile(self.active_file):
                with open(self.active_file) as prf_file:
                    active_name = prf_file.read().strip()

        return self.get(active_name)

    def export_workspace(self, workspace_name, file_name=None, copykeys=False):
        """Export content of workspace folder as gzipped tar file

        Replaces existing .tgz file
        """

        if workspace_name:
            workspace = self.get(workspace_name)
            if workspace is None:
                raise exceptions.IRWorkspaceMissing(workspace=workspace_name)
        else:
            workspace = self.get_active_workspace()
            if workspace is None:
                raise exceptions.IRNoActiveWorkspaceFound()

        fname = file_name or workspace.name

        # Copy workspace to not damage original,
        tmpdir = tempfile.mkdtemp()
        tmp_workspace_path = os.path.join(tmpdir,
                                          os.path.basename(workspace.path))

        try:
            shutil.copytree(workspace.path, tmp_workspace_path,
                            symlinks=True)
            tmp_workspace = Workspace(name=workspace.name,
                                      path=tmp_workspace_path)
            tmp_workspace._purge_paths(workspace.path)
            if copykeys:
                tmp_workspace._copy_outside_keys()
            with tarfile.open(fname + '.tgz', "w:gz") as tar:
                tar.add(tmp_workspace.path, arcname="./")
        finally:
            shutil.rmtree(tmpdir)

        print("Workspace {} is exported to file {}.tgz".format(workspace.name,
                                                               fname))

    def import_workspace(self, workspace_src, workspace_name=None):
        """Import workspace from gzipped tar file

        Workspace name should be unique
        Replaces workspace path placeholders with new ones in inventory

        :param workspace_src: Path/URL to a workspace tgz file
        :param workspace_name: Workspace name (same as the tgz file basename
        if not given)
        """
        original_src = workspace_src
        try:
            if not os.path.exists(workspace_src):
                urllib_ret = urllib2.urlopen(workspace_src)
                if urllib_ret.code is not 200:
                    raise exceptions.IRFailedToImportWorkspace(
                        'Got unexpected returned code ({}) from workspace '
                        'URL ({})'.format(urllib_ret.code, workspace_src))
                tmp_dir = tempfile.mkdtemp()
                workspace_src = \
                    os.path.join(tmp_dir, workspace_src.split('/')[-1])
                with open(workspace_src, 'w') as f:
                    f.write(urllib_ret.read())

            if workspace_name is None:
                basename = os.path.basename(workspace_src)
                workspace_name = ".".join(basename.split(".")[:-1])

            new_workspace = self.create(name=workspace_name)

            LOG.debug("Importing workspace from '{}' to '{}'".format(
                original_src, new_workspace.path))

            with tarfile.open(workspace_src) as tar:
                tar.extractall(path=new_workspace.path)

        except urllib2.HTTPError:
            raise exceptions.IRFailedToImportWorkspace(
                'Workspace URL not found - ({}) '.format(workspace_src))
        except tarfile.ReadError as e:
            raise exceptions.IRFailedToImportWorkspace(
                "{} tar{}".format(workspace_src, e.message))
        except ValueError as e:
            err_msg = "Workspace file not found"
            if 'unknown url' in e.message:
                err_msg += ' - If you entered a remote URL,' \
                           ' please make sure to provide its type'
            raise exceptions.IRFailedToImportWorkspace(err_msg)
        finally:
            if 'urllib_ret' in locals():
                urllib_ret.close()
            if 'tmp_dir' in locals():
                shutil.rmtree(tmp_dir)

        new_workspace._populate_paths()
        self.activate(new_workspace.name)

    def is_active(self, name):
        """Checks if workspace is active."""

        active = self.get_active_workspace()
        return False if active is None else active.name == name

    def cleanup(self, name):
        """Removes all the files from the workspace folder"""

        self.delete(name, keep_active_workspace_file=True)
        self.create(name)

    def node_list(self, workspace_name=None, group_name=None):
        """Lists nodes, connection types and groups from workspace's inventory

           nodes with connection type 'local' are skipped
           :param workspace_name: workspace name to list nodes from.
           :param group_name: filter nodes only on specific group
        """
        invent = self._get_inventory(workspace_name)

        if group_name:
            if group_name not in invent.groups:
                raise exceptions.IRGroupNotFoundException(group_name)

        hosts = invent.get_hosts(group_name or 'all')

        return [(host.name,
                 host.vars.get("ansible_host") or
                 host.vars.get("ansible_ssh_host"),
                 ', '.join(str(group) for group in host.groups
                           if str(group) not in EXCLUDED_GROUPS))
                for host in hosts
                if host.vars.get("ansible_connection") != "local"]

    def group_list(self, workspace_name=None):
        """Lists groups and nodes in them from workspace's inventory

           :param workspace_name: workspace name to list nodes from.
        """

        invent = self._get_inventory(workspace_name)

        groups = invent.list_groups()

        return [(group, ', '.join(str(host) for host in
                                  invent.get_groups_dict()[group]))
                for group in groups if group not in EXCLUDED_GROUPS]

    def _get_inventory(self, workspace_name=None):
        """Returns Inventory object for the provided workspace.
           Use active workspace as default

           :param workspace_name: workspace name to list nodes from.
        """
        workspace = self.get(
            workspace_name) if workspace_name else self.get_active_workspace()

        if workspace is None:
            if workspace_name is None:
                raise exceptions.IRNoActiveWorkspaceFound()
            else:
                raise exceptions.IRWorkspaceMissing(workspace=workspace_name)

        # need to have import here to avoid ansible patching
        from ansible.parsing.dataloader import DataLoader
        from ansible.inventory.manager import InventoryManager

        return InventoryManager(DataLoader(), sources=workspace.inventory)
