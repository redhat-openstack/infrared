#!/usr/bin/env python

from __future__ import print_function

__registry_port_map = {
    'docker-registry.engineering.redhat.com': '{mirror}:5000',
    'brew-pulp-docker01.web.prod.ext.phx2.redhat.com:8888': '{mirror}:5001',
    'docker-registry.upshift.redhat.com': '{mirror}:5003',
}


def container_mirror(registry_host, mirror):
    """Map urls for container registries to their local mirror version

    Based on if there is 'mirror' value provided (either short rdu2, tlv or full
    fqdn) translate any hostnames in 'registry_host' input to their mirror based
    counterpart.
    :param registry_host: string in which hostnames/urls of registries will be
                          replaced
    :param mirror: Either short alias of rhos-qe-mirror or full fqdn of the
                   mirror host.
    :return: (str) registry_host with urls converted to use local mirror
    """

    if not mirror:
        return registry_host

    if not ('.' in mirror):  # no hostname or ip, just short alias used (e.g. 'tlv', 'brq')
        mirror = ('rhos-qe-mirror-%s.usersys.redhat.com' % mirror)

    for (source, target) in __registry_port_map.items():
        registry_host = registry_host.replace(
            source,
            target.format(mirror=mirror))

    return registry_host


class FilterModule(object):
    def filters(self):
        return {
            'container_mirror': container_mirror,
        }


if __name__ == '__main__':
    import sys
    mirror = sys.argv[1]
    if len(sys.argv) > 2:
        # when '--inplace' is passed as first argument after 'mirror',
        # process all following arguments as path to files, and modify their
        # content
        if ('--inplace' == sys.argv[2]):
            for fpath in sys.argv[3:]:
                print('Processing %s ... ' % fpath, end='')
                with open(fpath, 'rw') as f:
                    cnt = f.read()
                    cnt = container_mirror(cnt, mirror)
                    f.write(cnt)
                print('done')
        else:
            # otherwise process each argument as registry url/host input itself
            for registry in sys.argv[2:]:
                print(container_mirror(registry, mirror))
    else:
        # just mirror specified in cli params, process stdin
        with open(sys.stdin) as stdin:
            print(container_mirror(sys.stdin.read(), mirror))
