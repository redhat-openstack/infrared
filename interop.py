#!/usr/bin/env python
import argparse
import os
import subprocess
import sys

import yaml

from cli.utils import dict_insert
from cli.yamls import dict_get


VIRSH_TOPO_MAP = {
    'host-address': 'hostname',
    'host-key': 'credentials.ssh_key_path',
    'host-user': 'credentials.user'
}

OSPD_CONF_MAP = {
    'product-version': 'version',
    'product-core-version': 'version'
}


def validate_path(yml_path):
    yml_path = os.path.expanduser(yml_path)
    if not os.path.exists(yml_path) or not os.path.isfile(yml_path):
        raise IOError("File not found: {}".format(yml_path))

    with open(yml_path) as f_obj:
        loaded_yml = yaml.safe_load(f_obj)
        if loaded_yml is None:
            raise IOError(
                "YAML file content isn't valid: {}".format(yml_path))
        return loaded_yml


def virsh_handler(topo_settings):

    virsh_exe = ['ir-provisioner', '--debug', 'virsh', '-vvvv']

    virsh_extras = [
        '--output=provision.yml',
        '--topology-nodes=1_undercloud,1_controller,1_compute'
    ]

    topo_args = ['--{}={}'.format(key, dict_get(topo_settings, val))
                 for key, val in VIRSH_TOPO_MAP.iteritems() if val]

    return virsh_exe + virsh_extras + topo_args


def ospd_handler(conf_settings):

    ospd_exe = ['ir-installer',  '--debug', 'ospd', '-vvvv']

    ospd_extras = [
        '--extra-vars=@provision.yml',
        '--output=install.yml',
        '--deployment-files={}'
        '/settings/installer/ospd/deployment/virt'.format(os.getcwd())
    ]

    conf_args = ['--{}={}'.format(key, dict_get(conf_settings, val))
                 for key, val in OSPD_CONF_MAP.iteritems() if val]

    return ospd_exe + ospd_extras + conf_args


def parse_args():
    """
    Parses the command line arguments using 'argparse' module

    :return: Namespace object
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--topology', type=validate_path,
                        help='Path to topology file')
    parser.add_argument('-c', '--configuration', type=validate_path,
                        help='Path to configuration file')
    parser.add_argument('-e', '--extra-vars', type=str,
                        help='Path to a YAML file contains extra vars')
    parser.add_argument('-o', '--output', type=str,
                        help='A path to an output file contains some relevant '
                             'data on the newly provisioned and installed '
                             'OpenStack environment')
    parser.add_argument('--dry-run', action='store_true',
                        help='Skip the playbooks execution stage')
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.topology and not args.configuration:
        raise ValueError("Wrong input! Please use at least one of the "
                         "following arguments: '--topology/--configuration'")

    # Generate 'virsh' conf file
    virsh_conf = 'virsh_default_conf.ini'
    p = subprocess.Popen('ir-provisioner virsh --generate-conf-file={}'.format(
        virsh_conf), shell=True)
    p.wait()

    virsh_cmd = virsh_handler(args.topology['osp_baremetal_host'][0])
    if args.dry_run:
        virsh_cmd.append('--dry-run')

    cleanup_cmd = virsh_cmd + ['--cleanup']
    print "Executing cleanup stage: {}".format(' '.join(cleanup_cmd))
    p = subprocess.Popen(cleanup_cmd)
    p.wait()
    if p.returncode:
        sys.exit(p.returncode)

    print "Executing provisioning stage: {}".format(virsh_cmd)
    p = subprocess.Popen(virsh_cmd)
    p.wait()
    if p.returncode:
        sys.exit(p.returncode)

    # Generate 'ospd' conf file
    ospd_conf = 'ospd_default_conf.ini'
    p = subprocess.Popen('ir-installer ospd --generate-conf-file={}'.format(
        ospd_conf), shell=True)
    p.wait()

    ospd_cmd = ospd_handler(args.configuration['openstack'])

    if args.extra_vars:
        ospd_cmd.append('--extra-vars=@{}'.format(args.extra_vars))
    if args.dry_run:
        ospd_cmd.append('--dry-run')

    print "Executing installing stage: ".format(ospd_cmd)
    p = subprocess.Popen(ospd_cmd)
    p.wait()
    if p.returncode:
        sys.exit(p.returncode)

    args.output = os.path.expanduser(os.path.abspath(args.output))

    # Copy rc files from the undercloud
    for rc_file in ('stackrc', 'overcloudrc'):
        cp_cmd = ('scp', '-F', 'ansible.ssh.config',
                  'root@undercloud-0:/home/stack/{}'.format(rc_file),
                  'interop_{}'.format(rc_file))
        p = subprocess.Popen(cp_cmd)
        p.wait()

    # Create the output file
    with open(args.output, 'w') as output_file:
        output_dict = {}

        with open('stackrc') as stackrc_file:
            for line in stackrc_file.read().splitlines():
                key, val = tuple(line.split(' ', 1)[-1].split('='))
                dict_insert(output_dict, val,
                            *'openstack.undercloud.{}'.format(key).split('.'))

        with open('overcloudrc') as stackrc_file:
            for line in stackrc_file.read().splitlines():
                key, val = tuple(line.split(' ', 1)[-1].split('='))
                dict_insert(output_dict, val,
                            *'openstack.overcloud.{}'.format(key).split('.'))

        yaml.safe_dump(output_dict, output_file, default_flow_style=False)


if __name__ == '__main__':
    main()
