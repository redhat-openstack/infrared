def sum_lengths(hostvars, nodes, fact):
    return sum(len(hostvars[node][fact]) for node in nodes)


class FilterModule(object):
    def filters(self):
        return {
            'sum_lengths': sum_lengths
        }
