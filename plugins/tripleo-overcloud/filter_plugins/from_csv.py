import csv


def csv_to_dict(value, delimiter=","):
    """
    >>> csv_to_dict("\\n".join(['"UUID","Name","State"',\
'"af6a3419","","power off"', \
'"c11b095b","foo","power on"']))
    [{'State': 'power off', 'UUID': 'af6a3419', 'Name': ''}, \
{'State': 'power on', 'UUID': 'c11b095b', 'Name': 'foo'}]
    """
    fieldnames = [i.strip('"') for i in value.splitlines()[0].split(delimiter)]
    return [i for i in csv.DictReader(value.splitlines()[1:],
                                      fieldnames=fieldnames)]


class FilterModule(object):

    def filters(self):
        return {
            'from_csv': csv_to_dict
        }
