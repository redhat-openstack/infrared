from __future__ import print_function

import os

from ansible.parsing.dataloader import DataLoader
from ansible import inventory
from ansible.playbook.play_context import MAGIC_VARIABLE_MAPPING
from ansible.vars import VariableManager

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

    for item in MAGIC_VARIABLE_MAPPING[varname]:
        result = hostobj.vars.get(item, "")
        if result:
            return result
    else:
        return default


def ssh_to_host(hostname):
    """ Compose cmd string of ssh and execute

        Uses Ansible to parse inventory file, gets ssh connection options
        :param hostname: str. Hostname from inventory
    """

    profile_manager = CoreServices.profile_manager()
    profile = profile_manager.get_active_profile()
    if profile is None:
        raise exceptions.IRNoActiveProfileFound()
    inventory_file = profile.inventory

    invent = inventory.Inventory(DataLoader(), VariableManager(),
                                 host_list=inventory_file)

    host = invent.get_host(hostname)
    if host is None:
        raise exceptions.IRSshException(
            "Host {} is not in inventory {}".format(hostname, inventory_file))

    if _get_magic_var(host, "connection") == "local":
        raise exceptions.IRSshException("Only ssh transport acceptable.")

    cmd = " ".join(["ssh {priv_key} {comm_args}",
                    "{extra_args} -p {port} {user}@{host}"])

    cmd_fields = {}
    cmd_fields["user"] = _get_magic_var(host, "remote_user", default="root")
    cmd_fields["port"] = _get_magic_var(host, "port", default=22)
    cmd_fields["host"] = _get_magic_var(host, "remote_addr")

    priv_key = _get_magic_var(host, "private_key_file")
    cmd_fields["priv_key"] = "-i {}".format(priv_key if priv_key else "")

    cmd_fields["comm_args"] = _get_magic_var(host, "ssh_common_args")
    cmd_fields["extra_args"] = _get_magic_var(host, "ssh_extra_args")

    LOG.debug("Establishing ssh connection to {}".format(cmd_fields["host"]))
    os.system(cmd.format(**cmd_fields))

    LOG.debug("Connection to {} closed".format(cmd_fields["host"]))
