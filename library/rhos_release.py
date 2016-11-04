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
    director_version:
        description:
            - the director version to install
    build_date:
        description:
            - specific puddle selection.
            This can be a known-symlink (Y1, Z1, GA, etc.), or
            a puddle date stamp in the form of YYYY-MM-DD.X
            (X = puddle generation # that day)
    core_version:
        description:
            - the core release name to install. Will be installed after
            director_version if it is specified.
    core_build_date:
        description:
            - the core build to install
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
notes:
    - requires rhos-release version 1.0.23
requirements: [ rhos-release ]
'''

EXAMPLE = '''
- name: Uninstalls release
  rhos_release: state=uninstall

- name: Install director release
  rhos_release:
    state: install
    director_version: 7-director
    build_date: latest
    pin_puddle: no
    distro_version: "{{ ansible_distribution_version }}"

- name: Install director and core releases
  rhos_release:
      state: install
      director_version: 8-director
      build_date: latest
      core_version: 7
      core_build_date: latest

- name: Get director and core puddle versions
  rhos_release:
      state: install
      director_version: 7-director
      build_date: latest
  register: director_release_results
  # show versions:
  debug: msg={{ director_release_results.releases.product.version }}
  debug: msg={{ director_release_results.releases.core.version }}

'''

POODLE_TYPES = {
    'weekly_stable': ['-W'],
    'daily-stable': ['-D'],
    'smoke': ['-C']
}

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
        _fail(module,"Found repo files in multiple directories %s" % dirs,
              cmd, out=stdout)
    repodir = dirs.pop() if len(dirs) > 0 else ''

    filenames = set(f["file"] for f in filenames)

    release_lines = [line for line in stdout.splitlines() if
                     line.startswith("# rhos-release ")]

    def released(line):
        pattern = re.compile(r'(?P<start># rhos-release )'
                             r'(?P<release>\d+)\s*'
                             r'(?P<director>-director)?\s*'
                             r'(?P<poodle>-d)?\s*'
                             r'-p (?P<version>\S+)'
                             )
        match = pattern.search(line)
        if not match:
            _fail(module, "Failed to parse release line %s" % line, cmd, out=stdout)
        return dict(
            release=match.group("release"),
            version=match.group("version"),
            repo_type="poodle" if match.group("poodle") else "puddle",
            channel="product" if match.group("director") else "core",
        )

    installed_releases = map(released, release_lines)
    return dict(
        repodir=repodir,
        files=list(filenames),
        releases={release['channel']: release for release in
                  installed_releases},
    )


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
            director_version=dict(),
            build_date=dict(),
            core_version=dict(),
            core_build_date=dict(),
            pin_puddle=dict(default=True),
            enable_poodle_repos=dict(default=False),
            poodle_type=dict(choices=POODLE_TYPES.keys()),
            target_directory=dict(),
            distro_version=dict(),
            source_hostname=dict(),
            enable_flea_repos=dict(default=False),
            one_shot_mode=dict(default=False),
        )
    )
    base_cmd = 'rhos-release'
    state = module.params['state']
    repo_directory = module.params['target_directory']
    release = module.params['director_version']
    puddle = module.params['build_date']
    # core params
    core_release = module.params['core_version']
    core_puddle = module.params['core_build_date']
    distro_version = module.params['distro_version']
    pin_puddle = module.params['pin_puddle']
    enable_poodle_repos = module.params['enable_poodle_repos']
    source_hostname = module.params['source_hostname']
    enable_flea_repos = module.params['enable_flea_repos']
    one_shot_mode = module.params['one_shot_mode']

    repo_args = ['-t', str(repo_directory)] if repo_directory else[]
    puddle = ['-p', str(puddle)] if puddle else []
    core_puddle = ['-p', str(core_puddle)] if core_puddle else []
    pin_puddle = ['-P'] if module.boolean(pin_puddle) else []
    enable_poodle_repos = ['-d'] if module.boolean(enable_poodle_repos) else []
    distro_version = ['-r', distro_version] if distro_version else []
    poodle_type = POODLE_TYPES.get(module.params['poodle_type'], [])
    source_hostname = ['-H', source_hostname] if source_hostname else []
    enable_flea_repos = ['-f'] if module.boolean(enable_flea_repos) else []
    one_shot_mode = ['-O'] if module.boolean(one_shot_mode) else []

    cmd = []
    if state == 'uninstall':
        cmd = [base_cmd, '-x']
        cmd.extend(repo_args)

    elif state in ['install', 'update']:
        # do some basic validateion
        releases = []

        if release:
            releases.append((release, puddle))
        if core_release:
            releases.append((core_release, core_puddle))

        if not releases:
            _fail("'director_version' or 'core_version' " +
                  "option should be specified.", cmd)

        for release, build in releases:
            if state == 'update':
                cmd.extend([base_cmd, '-u'])
            else:
                cmd.extend([base_cmd, release])

            cmd.extend(enable_poodle_repos)
            cmd.extend(enable_flea_repos)
            cmd.extend(poodle_type)
            cmd.extend(pin_puddle)
            cmd.extend(build)
            cmd.extend(distro_version)
            cmd.extend(source_hostname)
            cmd.extend(one_shot_mode)
            cmd.extend(repo_args)
            cmd.append(';')

    _run_command(module, ['sh', '-c', ' '.join(cmd)])


# import module snippets
from ansible.module_utils.basic import *


main()
