#!/usr/bin/python

# (c) 2014, Red Hat, Inc.
# Written by Yair Fried <yfried@redhat.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

from os import listdir
from os.path import isfile, join

DOCUMENTATION = '''
---
module: rhos-release
description:
    - Add/remove RHEL-OSP repo files on RHEL systems
options:
    state:
        description:
            - Whether to add (C(pinned), C(rolling)), or remove (C(absent)) repo files.
              If C(pinned) will grab the latest available version but pin the puddle
              version (dereference 'latest' links to prevent content from changing).
              If C(rolling) will grab latest in "rolling-release" and keep all links
              pointing to latest version.
        choices: ['pinned', 'rolling', 'absent']
        default: pinned
    release:
        description:
            - release name to find
    dest:
        description:
            - target directory for repo files
        default: "/etc/yum.repos.d"
    distro:
        description:
            - override the default RHEL version
    repo_type:
        description:
            - Controls the repo type C(puddle) or C(poodle)
        choices: ['puddle', 'poodle']
        default: puddle
    version:
        description:
            - Specific puddle/poodle selection.
              This can be a known-symlink (Y1, Z1, GA, etc.), or
              a puddle date stamp in the form of YYYY-MM-DD.X


notes:
    - requires rhos-release version 1.0.23
requirements: [ rhos-release ]
'''

Examples = '''
- name: Remove all RHEL-OSP repo files.
  rhos-release: state=absent

- name: Add latest RHEL-OSP repo files for for RHEL-OSP 7 and pin version.
  rhos-release: release=7

- name: Add latest RHEL-OSP repo files for for RHEL-OSPd 7 and pin version.
  rhos-release: release=7_director

- name: Add latest RHEL-OSP repo files for for RHEL-OSP 7 unpinned (rolling release).
  rhos-release: release=7 state=rolling

- name: Add latest RHEL-OSP repo files for for RHEL-OSPd 7 unpinned (rolling release).
  rhos-release: release=7_director state=rolling

'''


REPODST = "/etc/yum.repos.d"


def get_repo_list(repodst):
    return [f for f in listdir(repodst) if isfile(join(repodst, f)) and
            f.startswith('rhos-release-') and f.endswith(".repo")]


def _remove_repos(module, base_cmd):
    """ Remove RHEL-OSP repos files"""

    repodst = REPODST
    cmd = [base_cmd, '-x']

    if module.params["dest"]:
        repodst = module.params["dest"]
        cmd.extend(["-t", module.params["dest"]])

    repo_files = get_repo_list(repodst)
    if repo_files:

        rc, out, err = module.run_command(cmd)
        if rc == "127":
            module.fail_json(msg='Requires rhos-release installed. %s: %s' % (cmd, err))
        elif rc:
            module.fail_json(msg='Error: %s: %s' % (cmd, err))
        empty_repo_files = get_repo_list(repodst)
        if empty_repo_files:
            module.fail_json(msg="Failed to remove files: %s" % empty_repo_files)
        module.exit_json(changed=True, deleted_files=repo_files)
    else:
        module.exit_json(changed=False, msg="No repo files found")


def _parse_output(module, stdout):
    """Parse rhos-release stdout.

    lines starting with "Installed":
        list of repo files created.
        verify all files are created in the same directory.

    lines starting with "# rhos-release":
        Installed channel details
            release=release number (should match "release" input),
            version=version tag of release,
            repo_type="poodle"/"puddle",
            channel=ospd/core,
        verify no more than 2 channels installed - core and/or ospd

    :return: dict(
        repodir=absolute path of directory where repo files were created,
        files=list of repo files created (filter output duplications),
        releases=list of channels (see channel details) installed,
        stdout=standard output of rhos-release,
        )
    """
    file_lines = [line for line in stdout.splitlines() if line.startswith("Installed")]

    def installed(line):
        pattern = re.compile(r'(?P<start>Installed: )(?P<filename>\S+)')
        match = pattern.search(line)
        if not match:
            module.fail_json("Failed to parse line %s" % line)
        filename = os.path.abspath(match.group("filename"))
        return dict(
            file=os.path.basename(filename),
            repodir=os.path.dirname(filename)
        )

    filenames = map(installed, file_lines)
    dirs = set(f["repodir"] for f in filenames)
    if len(dirs) > 1:
        module.fail_json("Found repo files in multiple directories %s" % dirs)
    repodir = dirs.pop()
    filenames = set(f["file"] for f in filenames)

    release_lines = [line for line in stdout.splitlines() if line.startswith("# rhos-release ")]

    def released(line):
        pattern = re.compile(r'(?P<start># rhos-release )'
                             r'(?P<release>\d+)\s*'
                             r'(?P<director>-director)?\s*'
                             r'(?P<poodle>-d)?\s*'
                             r'-p (?P<version>\S+)'
                             )
        match = pattern.search(line)
        if not match:
            module.fail_json("Failed to parse line %s" % line)
        return dict(
            release=match.group("release"),
            version=match.group("version"),
            repo_type="poodle" if match.group("poodle") else "puddle",
            channel="ospd" if match.group("director") else "core",
        )

    installed_releases = map(released, release_lines)
    if len(installed_releases) > 2 or (len(installed_releases) == 2 and
                                       set(r["channel"] for r in installed_releases) != set(("ospd", "core"))):
        module.fail_json(msg="Can't handle more than 2 channels. 1 core, 1 ospd. Found %s" % installed_releases)

    return dict(
        repodir=repodir,
        files=list(filenames),
        releases=installed_releases,
        stdout=stdout.splitlines()
    )


def _get_latest_repos(module, base_cmd, state, release):
    """ Add RHEL-OSP latest repos """

    if not release:
        module.fail_json(msg="Missing release number for '%s' state" % state)
    cmd = [base_cmd, release]
    if state == "pinned":
        cmd.append('-P')
    if module.params["dest"]:
        cmd.extend(["-t", module.params["dest"]])
    if module.params["distro"]:
        cmd.extend(["-r", module.params["distro"]])
    if module.params["repo_type"] == "poodle":
        cmd.append("-d")
    if module.params["version"]:
        cmd.extend(["-p", module.params["version"]])

    rc, out, err = module.run_command(cmd)
    if rc == "127":
        module.fail_json(msg='Requires rhos-release installed. %s: %s' % (cmd, err))
    elif rc:
        module.fail_json(msg='Error: %s: %s' % (cmd, err))
    summary = _parse_output(module, out)
    module.exit_json(changed=True, **summary)


def main():
    """ Main """
    module = AnsibleModule(
        argument_spec = dict(
            state=dict(default="pinned", choices=['absent', 'pinned', 'rolling'], required=False),
            release=dict(required=True),
            dest=dict(default=None, required=False),
            distro=dict(default=None, required=False),
            repo_type=dict(default="puddle", choices=['puddle', 'poodle'], required=False),
            version=dict(default=None, required=False)
        )
    )
    state = module.params["state"]
    release = module.params["release"]

    base_cmd = "rhos-release"
    if state == "absent":
        _remove_repos(module, base_cmd)
    else:
        _get_latest_repos(module, base_cmd, state, release)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
