from __future__ import print_function

import os

from ansible.parsing.dataloader import DataLoader
from ansible import inventory
from ansible.playbook.play_context import MAGIC_VARIABLE_MAPPING
from ansible.vars import VariableManager

from infrared.core.services import CoreServices
from infrared.core.utils import logger


LOG = logger.LOG


def _get_magic_var(varname, hostobj, defaultres=""):
    for item in MAGIC_VARIABLE_MAPPING[varname]:
        result = hostobj.vars.get(item, "")
        if result:
            return result
    else:
        return defaultres


def ssh_to_host(hostname):

    profile_manager = CoreServices.profile_manager()
    profile = profile_manager.get_active_profile()
    if profile is None:
        LOG.error("There is no active profile. Please activate one.")
        return
    inventory_file = profile.inventory

    invent = inventory.Inventory(DataLoader(), VariableManager(),
                                 host_list=inventory_file)

    host = invent.get_host(hostname)
    if host is None:
        LOG.error("Host %s is not in inventory %s" % (hostname,
                                                      inventory_file))
        return

    if _get_magic_var("connection", host) == "local":
        LOG.error("Only ssh transport available.")
        return

    cmd = " ".join(["%(passwd)s ssh %(priv_key)s %(comm_args)s",
                    "%(extra_args)s -p %(port)d %(user)s@%(host)s"])

    cmd_fields = {}
    cmd_fields["user"] = _get_magic_var("remote_user", host, "root")
    cmd_fields["port"] = _get_magic_var("port", host, 22)
    cmd_fields["host"] = _get_magic_var("remote_addr", host)

    priv_key = _get_magic_var("private_key_file", host)
    cmd_fields["priv_key"] = "-i %s" % priv_key if priv_key else ""

    cmd_fields["comm_args"] = _get_magic_var("ssh_common_args", host)
    cmd_fields["extra_args"] = _get_magic_var("ssh_extra_args", host)

    passwd = _get_magic_var("password", host)
    cmd_fields["passwd"] = "sshpass -p %s" % passwd if passwd else ""

    LOG.info("== Establishing ssh connection to %s ==" % cmd_fields["host"])

    os.system(cmd % cmd_fields)

    LOG.info("-- Connection to %s closed --" % cmd_fields["host"])
