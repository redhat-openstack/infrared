#!/usr/bin/python

# (c) 2014, Red Hat, Inc.
# Written by Yair Fried <yfried@redhat.com> and Oleksii Baranov <obaranov@redhat.com>
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
import os
import re
from ansible.module_utils.basic import AnsibleModule


DOCUMENTATION = '''
---
module: rhos-release
description:
    - Add/remove RHEL-OSP repo files on RHEL systems
options:
    state:
        description:
            - Whether to install (C(install)) release, remove (C(uninstall)) or update
              (C(update)) repo files.
        choices: ['install', 'uninstall', 'update']
    version:
        description:
            - the core release name to install.
    build_date:
        description:
            - specific puddle selection.
              This can be a known-symlink (Y1, Z1, GA, etc.), or
              a puddle date stamp in the form of YYYY-MM-DD.X
              (X = puddle generation # that day)
    director:
        description:
            - Install director packages. Applicable for OSP 7-9 only.
        default: 'yes'
    target_directory:
        description:
            - target directory for repo files
    distro_version:
        description:
            - override the default RHEL version
    enable_poodle_repos:
        description:
            - specifieis whether the poodle repo should be enables or not.
        default: 'no'
    enable_testing_repos:
        description:
            - specifies whether to enable testing (pending) repositories.
        default: 'no'
    poodle_type:
        description:
            - specifies the poodle to use. Should be used with
              (C(enable_poodle_repos)) set to true. Implies (C(build)) value.
        choices: ['weekly_stable', 'daily-stable', 'smoke']
    pin_puddle:
        description:
            - pin puddle (dereference 'latest' links to prevent content
              from changing)
        default: 'yes'
    source_hostname:
        description:
            - the host name to override for download servers.
              Ignores empty hostname.
    enable_flea_repos:
        description:
            - specifieis whether the flea repos should be enables or not.
        default: 'no'
    one_shot_mode:
        description:
            - One-shot mode.  Only install a specific repository;
              do not install dependent repositories.
        default: 'no'
    buildmods:
        description:
            - List of flags that will be enabled. only works with pin puddle,
              flea-repos, unstable and cdn
notes:
    - requires rhos-release version 1.0.23
requirements: [ rhos-release ]
'''

EXAMPLE = '''
- name: Uninstalls release
  rhos_release: state=uninstall

- name: Install OSPD release
  rhos_release:
    state: install
    version: 8
    build_date: latest
    pin_puddle: no
    distro_version: "{{ ansible_distribution_version }}"
'''

POODLE_TYPES = {
    'weekly_stable': ['-W'],
    'daily-stable': ['-D'],
    'smoke': ['-C']
}

LATEST_INSTALLED_FILE = "/etc/yum.repos.d/latest-installed"


def _parse_output(module, cmd, stdout):
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
    file_lines = [line for line in stdout.splitlines() if
                  line.startswith("Installed")]

    def installed(line):
        pattern = re.compile(r'(?P<start>Installed: )(?P<filename>\S+)')
        match = pattern.search(line)
        if not match:
            _fail(module, "Failed to parse line %s" % line, cmd, out=stdout)
        filename = os.path.abspath(match.group("filename"))
        return dict(
            file=os.path.basename(filename),
            repodir=os.path.dirname(filename)
        )

    filenames = map(installed, file_lines)
    dirs = set(f["repodir"] for f in filenames)
    if len(dirs) > 1:
        _fail(module, "Found repo files in multiple directories %s" % dirs,
              cmd, out=stdout)
    repodir = dirs.pop() if len(dirs) > 0 else ''

    filenames = set(f["file"] for f in filenames)

    release_lines = [line for line in stdout.splitlines() if
                     line.startswith("# rhos-release ")]

    def released(line):
        pattern = re.compile(r'(?P<start># rhos-release )'
                             r'(?P<release>\d+)(?P<trunk>(-trunk)?)\s*'
                             r'(?P<director>-director)?\s*'
                             r'(?P<poodle>-d)?\s*'
                             r'(-p (?P<version>\S*))?'
                             )
        match = pattern.search(line)
        if not match:
            _fail(module, "Failed to parse release line %s" % line,
                  cmd, out=stdout)
        return dict(
            release=match.group("release"),
            version=match.group("version") or 'undetermined!',
            repo_type="poodle" if match.group("poodle") else "puddle",
            channel="director" if match.group("director") else "core",
        )

    installed_releases = map(released, release_lines)
    ret_dict = dict(
        repodir=repodir,
        files=list(filenames)
    )
    if module.params['buildmods'] is not None \
            and 'cdn' in module.params['buildmods']:
        ret_dict['releases'] = {"core": dict(
            release=module.params['release'],
            version='cdn',
            repo_type='cdn',
            channel='core'
            )}
    else:
        ret_dict['releases'] = dict((release['channel'], release)
                                    for release in installed_releases)

    return ret_dict


def do_build_discover():
    """
    Discovers currently installed build by reading
    "/etc/yum.repos.d/latest-installed"
    """

    import os.path
    result = ""
    if os.path.isfile(LATEST_INSTALLED_FILE):
        with open(LATEST_INSTALLED_FILE) as fd:
            regex = re.search('.* -p (.*)', fd.read())
            if regex and regex.group(1):
                result = regex.group(1)

    return result


def wrap_results(res_dict, cmd, rc, out, err):
    """
    Wraps ansible response with addtional information usefull for debug.

    This will also print into console command executed, stderr and stdout.
    """
    if res_dict is None:
        res_dict = dict()

    res_dict['stdout'] = out
    res_dict['stderr'] = err
    res_dict['rc'] = rc
    res_dict['cmd'] = ' '.join(cmd)

    return res_dict


def _run_command(module, cmd):
    return_code, out, err = module.run_command(cmd)
    if return_code == "127":
        _fail(module, "Requires rhos-release installed",
              cmd, return_code, out, err)
    elif return_code:
        _fail(module, 'Error', cmd, return_code, out, err)

    summary = _parse_output(module, cmd, out)
    module.exit_json(changed=True, **wrap_results(
        summary, cmd, return_code, out, err))


def _fail(module, msg, cmd, return_code=-1, out='', err=''):
    """
    Fails module execution.
    """
    module.fail_json(
        **wrap_results(dict(msg=msg), cmd, return_code, out, err))


def main():
    """ Main """
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default="install",
                       choices=['install', 'uninstall', 'update']),
            release=dict(),
            build_date=dict(),
            director=dict(type='bool', default=True),
            director_build_date=dict(),
            pin_puddle=dict(default=True),
            enable_poodle_repos=dict(default=False),
            poodle_type=dict(choices=POODLE_TYPES.keys()),
            target_directory=dict(),
            distro_version=dict(),
            source_hostname=dict(),
            enable_flea_repos=dict(default=False),
            one_shot_mode=dict(default=False),
            buildmods=dict(type='list'),
            discover_build=dict(type='bool', default=False),
            enable_testing_repos=dict()
        )
    )
    base_cmd = 'rhos-release'
    state = module.params['state']
    repo_directory = module.params['target_directory']
    release = module.params['release']
    puddle = module.params['build_date']
    director = module.params['director']
    director_puddle = module.params['director_build_date']
    distro_version = module.params['distro_version']
    pin_puddle = module.params['pin_puddle']
    enable_poodle_repos = module.params['enable_poodle_repos']
    source_hostname = module.params['source_hostname']
    enable_flea_repos = module.params['enable_flea_repos']
    one_shot_mode = module.params['one_shot_mode']
    buildmods = module.params['buildmods']
    discover_build = module.params['discover_build']
    enable_testing_repos = module.params['enable_testing_repos']

    repo_args = ['-t', str(repo_directory)] if repo_directory else[]

    if discover_build and not puddle:
        puddle = do_build_discover()

    puddle = ['-p', str(puddle)] if puddle else []
    pin_puddle = ['-P'] if module.boolean(pin_puddle) else []
    enable_poodle_repos = ['-d'] if module.boolean(enable_poodle_repos) else []
    director_puddle = ['-p', str(director_puddle)] if director_puddle else []
    distro_version = ['-r', distro_version] if distro_version else []
    poodle_type = POODLE_TYPES.get(module.params['poodle_type'], [])
    source_hostname = ['-H', source_hostname] if source_hostname else []
    enable_flea_repos = ['-f'] if module.boolean(enable_flea_repos) else []
    one_shot_mode = ['-O'] if module.boolean(one_shot_mode) else []
    enable_testing_repos = ['-T', str(enable_testing_repos)] if enable_testing_repos else []

    mods = {
        'pin': '-P',
        'flea': '-f',
        'unstable': '--unstable',
        'cdn': ''
    }

    cmd = []
    if state == 'uninstall':
        cmd = [base_cmd, '-x']
        cmd.extend(repo_args)

    elif state in ['install', 'update']:
        if not release:
            _fail(module, "'release' option should be specified.", cmd)

        if "cdn" in buildmods:
            release = str(release) + "-cdn"

        releases = [(str(release), puddle)]
        try:
            if 10 > int(release) > 6 and director:
                releases = [(str(release) + '-director', director_puddle)] + releases
        except ValueError:
            # RDO versions & CDN shouldn't try to get director repos
            pass

        for release, build in releases:
            if state == 'update':
                cmd.extend([base_cmd, '-u'])
            else:
                cmd.extend([base_cmd, release])

            if not(len(buildmods) == 1 and 'none' in buildmods):
                for buildmod in buildmods:
                    cmd.append(mods[buildmod.lower()])

            cmd.extend(enable_poodle_repos)
            # cmd.extend(enable_flea_repos)
            cmd.extend(poodle_type)
            # cmd.extend(pin_puddle)
            cmd.extend(build)
            cmd.extend(distro_version)
            cmd.extend(source_hostname)
            cmd.extend(one_shot_mode)
            cmd.extend(enable_testing_repos)
            cmd.extend(repo_args)
            cmd.append(';')

    _run_command(module, ['sh', '-c', ' '.join(cmd)])


# import module snippets
from ansible.module_utils.basic import *  # noqa


main()
