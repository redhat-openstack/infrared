#!/usr/bin/env python

import argparse
import time
import tarfile
import re
import tempfile
import os

ARCHIVE_FILE_NAME = 'archive-{suffix}.tar'
ARCHIVE_FILES_MAP = dict(
    inventory='hosts-{suffix}',
    ssh_conf='ansible.ssh.config.{suffix}'
)


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
    parser.add_argument('--ssh_conf', type=str, default='ansible.ssh.config',
                        help='SSH config file to be archived')
    parser.add_argument('--debug', action='store_true',
                        help='run in debug mode')
    return parser.parse_args()


def main():
    args = parse_args()
    args_d = vars(args)

    if args.suffix is None:
        # Generate time based suffix
        args.suffix = str(int(time.time()))

    global ARCHIVE_FILE_NAME
    ARCHIVE_FILE_NAME = ARCHIVE_FILE_NAME.format(suffix=args.suffix)

    files_content = {}
    for f in ('inventory', 'ssh_conf'):
        if not os.path.exists(args_d[f]):
            from cli.exceptions import IRFileNotFoundException
            raise IRFileNotFoundException(args_d[f])
        args_d[f] = os.path.expanduser(args_d[f])
        if os.path.islink(args_d[f]):
            args_d[f] = os.readlink(args_d[f])
        with open(args_d[f]) as f_obj:
            files_content[f] = f_obj.read()

    key_cnt = 0
    ssh_keys_map = {}
    ssh_keys = {key_line.split()[-1] for key_line in
                re.findall('IdentityFile .*', files_content['ssh_conf'])}
    for ssh_key in ssh_keys:
        key_cnt += 1
        ssh_keys_map[ssh_key] = 'id_rsa-{suffix}-{key_cnt}'.format(
            suffix=args.suffix, key_cnt=key_cnt)
        for file_content_key in files_content.keys():
            files_content[file_content_key] = re.sub(ssh_key, ssh_keys_map[
                ssh_key].split('/')[-1], files_content[file_content_key])

    with tarfile.open(ARCHIVE_FILE_NAME, 'w') as tar:

        for ssh_key in ssh_keys_map:
            tar.add(os.path.expanduser(ssh_key), ssh_keys_map[ssh_key])

        for file_to_archive in ARCHIVE_FILES_MAP.keys():
            with tempfile.NamedTemporaryFile(mode='w+r') as tmp_file:
                tmp_file.write(files_content[file_to_archive])
                tmp_file.file.seek(0)
                tar.add(tmp_file.name,
                        ARCHIVE_FILES_MAP[file_to_archive].format(
                            suffix=args.suffix))

    print "Archive file has been successfully created: {archive_file}".format(
        archive_file=ARCHIVE_FILE_NAME)


if __name__ == '__main__':
    main()
