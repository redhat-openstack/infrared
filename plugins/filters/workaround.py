from ansible import utils


def workaround_enabled(workarounds, *bugs, **kw):
    if not isinstance(workarounds, dict):
        return False

    for bug_id in bugs:
        enabled = workarounds.get(bug_id, {}).get('enabled', False)
        if not utils.boolean(enabled):
            return False
    return True


class FilterModule(object):

    def filters(self):
        return {
            'bug': workaround_enabled,
        }
