from os import path

import ansible.color
import ansible.inventory
import ansible.playbook
import ansible.utils
from ansible import callbacks

from cli import conf, exceptions, logger

LOG = logger.LOG
CONF = conf.config

VERBOSITY = 0
HOSTS_FILE = "hosts"
PLAYBOOKS = ["provision", "install", "test", "collect-logs", "cleanup"]

assert "playbooks" == path.basename(
    CONF.get('defaults', 'playbooks')), "Bad path to playbooks"


# ansible-playbook
# https://github.com/ansible/ansible/blob/devel/bin/ansible-playbook

# From ansible-playbook
def colorize(lead, num, color):
    """ Print 'lead' = 'num' in 'color' """

    if num != 0 and color is not None:
        return "%s%s%-15s" % (ansible.color.stringc(lead, color),
                              ansible.color.stringc("=", color),
                              ansible.color.stringc(str(num), color))
    else:
        return "%s=%-4s" % (lead, str(num))


def hostcolor(host, stats, color=True):
    if color:
        if stats['failures'] != 0 or stats['unreachable'] != 0:
            return "%-37s" % ansible.color.stringc(host, 'red')
        elif stats['changed'] != 0:
            return "%-37s" % ansible.color.stringc(host, 'yellow')
        else:
            return "%-37s" % ansible.color.stringc(host, 'green')
    return "%-26s" % host


def ansible_playbook(playbook, args, inventory="local_hosts"):
    """
    Wraps the 'ansible-playbook' CLI.
     :playbook: the playbook to invoke
     :args: all arguments passed for the playbook
     :inventory: the inventory file to use, default: local_hosts
    """

    if not playbook:
        LOG.error("No playbook to execute (%s)" % PLAYBOOKS)

        # TODO: remove all IRexceptions and change to regular Python exceptions
        raise exceptions.IRFileNotFoundException

    print "Executing Playbook: %s" % playbook

    ansible.utils.VERBOSITY = args['verbose']
    path_to_playbook = path.join(CONF.get('defaults', 'playbooks'), playbook)

    # From ansible-playbook:
    stats = callbacks.AggregateStats()
    playbook_cb = callbacks.PlaybookCallbacks(verbose=ansible.utils.VERBOSITY)
    if args.get('step'):
        # execute step by step
        playbook_cb.step = args.step

    if args.get('start_at'):
        # start execution at a specific task
        playbook_cb.start_at = args.start_at

    runner_cb = callbacks.PlaybookRunnerCallbacks(
        stats,
        verbose=ansible.utils.VERBOSITY
    )

    module_path = CONF.get('defaults', 'modules')

    pb = ansible.playbook.PlayBook(
        # From ansible-playbook:
        playbook=path_to_playbook,
        inventory=ansible.inventory.Inventory(inventory),
        extra_vars=args['settings'],
        callbacks=playbook_cb,
        runner_callbacks=runner_cb,
        stats=stats,
        module_path=module_path
    )

    failed_hosts = []
    unreachable_hosts = []

    if args['verbose']:
        ansible_cmd = ["ansible-playbook"]
        if module_path:
            ansible_cmd.append("-M " + module_path)
        ansible_cmd.append("-" + "v" * args['verbose'])
        ansible_cmd.append("-i " + inventory)
        extra_vars = args['output'] or "<path to settings file>"
        ansible_cmd.append("--extra-vars @" + extra_vars)
        ansible_cmd.append(path_to_playbook)
        print "ANSIBLE COMMAND: " + " ".join(ansible_cmd)

    pb.run()

    hosts = sorted(pb.stats.processed.keys())
    callbacks.display(callbacks.banner("PLAY RECAP"))
    playbook_cb.on_stats(pb.stats)

    for host in hosts:
        status = pb.stats.summarize(host)
        if status['failures'] > 0:
            failed_hosts.append(host)
        if status['unreachable'] > 0:
            unreachable_hosts.append(host)

    retries = failed_hosts + unreachable_hosts

    if len(retries) > 0:
        filename = pb.generate_retry_inventory(retries)
        if filename:
            callbacks.display(
                "           to retry, use: --limit @%s\n" % filename)

    for host in hosts:
        status = pb.stats.summarize(host)

        callbacks.display("%s : %s %s %s %s" % (
            hostcolor(host, status),
            colorize('ok', status['ok'], 'green'),
            colorize('changed', status['changed'], 'yellow'),
            colorize('unreachable', status['unreachable'], 'red'),
            colorize('failed', status['failures'], 'red')), screen_only=True)

        callbacks.display("%s : %s %s %s %s" % (
            hostcolor(host, status, False),
            colorize('ok', status['ok'], None),
            colorize('changed', status['changed'], None),
            colorize('unreachable', status['unreachable'], None),
            colorize('failed', status['failures'], None)), log_only=True)

    print ""
    if len(failed_hosts) > 0:
        raise exceptions.IRPlaybookFailedException(
            playbook, "Failed hosts: %s" % failed_hosts)
    if len(unreachable_hosts) > 0:
        raise exceptions.IRPlaybookFailedException(
            playbook, "Unreachable hosts: %s" % unreachable_hosts)
