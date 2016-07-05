#!/usr/bin/env python

import argparse
import datetime
import logging
import time
import tarfile
import re
import tempfile
import os

from cli.logger import LOG

ARCHIVE_FILE_NAME = 'IR-Archive-{suffix}.tar'
ARCHIVE_FILES_MAP = dict(
    inventory='hosts-{suffix}',
    ssh_conf='ansible.ssh.config.{suffix}'
)
TIME_FORMAT = '%Y-%m-%d_%H-%M-%S'


def parse_args():
    """
    Parses the command line arguments using 'argparse' module

    :return: Namespace object
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--suffix', type=str,
                        help='suffix to be added to the archive file')
    parser.add_argument('--inventory', type=str, default='hosts',
                        help='inventory file to be archived')
    parser.add_argument('--ssh-conf', type=str, default='ansible.ssh.config',
                        help='SSH config file to be archived')
    parser.add_argument('--dest-dir', type=str, default='',
                        help='Directory to save the archive file in')
    parser.add_argument('--debug', action='store_true',
                        help='run in debug mode')
    return parser.parse_args()


def get_file_content(file_path):
    file_path = os.path.expanduser(file_path)
    if not os.path.exists(file_path):
        from cli.exceptions import IRFileNotFoundException
        raise IRFileNotFoundException(file_path)
    if os.path.islink(file_path):
        file_path = os.readlink(file_path)
    with open(file_path) as f_obj:
        file_content = f_obj.read()
    return file_content


def main():
    args = parse_args()

    if args.suffix is None:
        # Generate time based suffix
        args.suffix = datetime.datetime.fromtimestamp(
            time.time()).strftime(TIME_FORMAT)

    global ARCHIVE_FILE_NAME
    ARCHIVE_FILE_NAME = ARCHIVE_FILE_NAME.format(suffix=args.suffix)

    files_content = {}
    for file_arg in ('inventory', 'ssh_conf'):
        files_content[file_arg] = get_file_content(getattr(args, file_arg))

    ssh_keys_map = {}
    ssh_keys = set(key_line.split()[-1] for key_line in
                   re.findall('IdentityFile .*', files_content['ssh_conf']))

    for key_idx, ssh_key in enumerate(ssh_keys):
        ssh_keys_map[ssh_key] = 'id_rsa-{suffix}-{key_idx}'.format(
            suffix=args.suffix, key_idx=key_idx)
        for file_content_key in files_content.keys():
            files_content[file_content_key] = re.sub(
                ssh_key,
                os.path.basename(ssh_keys_map[ssh_key]),
                files_content[file_content_key]
            )

    with tarfile.open(
            os.path.join(args.dest_dir, ARCHIVE_FILE_NAME), 'w') as tar:

        for ssh_key in ssh_keys_map:
            tar.add(os.path.expanduser(ssh_key), ssh_keys_map[ssh_key])

        for file_to_archive in ARCHIVE_FILES_MAP.keys():
            with tempfile.NamedTemporaryFile(mode='w+r') as tmp_file:
                tmp_file.write(files_content[file_to_archive])
                tmp_file.file.seek(0)
                tar.add(tmp_file.name,
                        ARCHIVE_FILES_MAP[file_to_archive].format(
                            suffix=args.suffix))

        LOG.setLevel(logging.INFO)
        LOG.info(
            "Archive file has been successfully created: "
            "{archive_file_name}".format(archive_file_name=tar.name))


if __name__ == '__main__':
    main()
