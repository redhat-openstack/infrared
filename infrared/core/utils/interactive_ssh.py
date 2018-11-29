from __future__ import print_function

import os

from infrared.core.services import CoreServices
from infrared.core.utils import exceptions
from infrared.core.utils import logger


LOG = logger.LOG


def _get_magic_var(hostobj, varname, default=""):
    """ Use Ansible coordination of inventory format versions

        :param hostobj: parsed Ansible host object
        :param varname: key of MAGIC_VARIABLE_MAPPING, representing
                        variations of Ansible inventory parameter
        :param default: value, that will be returned if 'varname' is
                        not set in inventory
    """
    from ansible.constants import MAGIC_VARIABLE_MAPPING
    for item in MAGIC_VARIABLE_MAPPING[varname]:
        result = hostobj.vars.get(item, "")
        if result:
            return result
    else:
        return default


def ssh_to_host(hostname, remote_command=None):
    """ Compose cmd string of ssh and execute

        Uses Ansible to parse inventory file, gets ssh connection options
        :param hostname: str. Hostname from inventory
    """

    workspace_manager = CoreServices.workspace_manager()
    workspace = workspace_manager.get_active_workspace()
    if workspace is None:
        raise exceptions.IRNoActiveWorkspaceFound()
    inventory_file = workspace.inventory

    from ansible.parsing.dataloader import DataLoader
    from ansible.inventory.manager import InventoryManager
    invent = InventoryManager(DataLoader(), sources=inventory_file)

    host = invent.get_host(hostname)
    if host is None:
        raise exceptions.IRSshException(
            "Host {} is not in inventory {}".format(hostname, inventory_file))

    if _get_magic_var(host, "connection") == "local":
        raise exceptions.IRSshException("Only ssh transport acceptable.")

    cmd = " ".join(["ssh {priv_key} {comm_args}",
                    "{extra_args} -p {port} -t {user}@{host}"])

    cmd_fields = {}
    cmd_fields["user"] = _get_magic_var(host, "remote_user", default="root")
    cmd_fields["port"] = _get_magic_var(host, "port", default=22)
    cmd_fields["host"] = _get_magic_var(host, "remote_addr")

    priv_key = _get_magic_var(host, "private_key_file")
    # NOTE(yfried):
    # ssh client needs key to be in the directory you're running one from
    # ('ssh -i id_rsa ...') or to be provided by absolute path.
    # assume paths are relative to inventory file.
    priv_key = os.path.join(os.path.abspath(os.path.dirname(inventory_file)),
                            priv_key)
    if not os.access(priv_key, os.R_OK):
        raise exceptions.IRSshException("Private key file mentioned does not "
                                        "exist: {}".format(priv_key))

    if priv_key:
        cmd_fields["priv_key"] = "-i {}".format(priv_key)
    else:
        cmd_fields["priv_key"] = ""

    cmd_fields["comm_args"] = _get_magic_var(host, "ssh_common_args")
    cmd_fields["extra_args"] = _get_magic_var(host, "ssh_extra_args")

    compiled_cmd = cmd.format(**cmd_fields)
    LOG.debug("Establishing ssh connection to {} using: {}".format(cmd_fields["host"], compiled_cmd))
    if remote_command is not None:
        compiled_cmd = " ".join(
            [compiled_cmd, '"{}"'.format(remote_command)])

    result = os.WEXITSTATUS(os.system(compiled_cmd))
    LOG.debug("Connection to {} closed".format(cmd_fields["host"]))
    return result
