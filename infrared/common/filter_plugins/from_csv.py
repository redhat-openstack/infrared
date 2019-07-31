import csv
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

def csv_to_dict(string, delimiter=','):
    """ Creates a list of dicts from a string in the format:
                            [
        "a, b, c\n"\            {'a': '1', 'b': '2', 'c': '3'},
        "1, 2, 3\n"\  -->       {'a': '4', 'b': '5', 'c': '6'},
        "4, 5, 6\n"\            {'a': '7', 'b': '8', 'c': '9'}
        "7, 8, 9\n"         ]
    >>> csv_to_dict("\n".join(['"UUID","Name","State"',\
    '"af6a3419","","power off"', \
    '"c11b095b","foo","power on"']))
    [{'State': 'power off', 'UUID': 'af6a3419', 'Name': ''}, \
    {'State': 'power on', 'UUID': 'c11b095b', 'Name': 'foo'}]
    >>> csv_to_dict('"UUID","Name","State"\n')
    []
    >>> csv_to_dict('')
    []
    >>> csv_to_dict('"UUID","Name","State"')
    []
    """
    if not string:
        return []
    reader = csv.reader(StringIO(string), delimiter=delimiter)
    column_index_to_name_map = [column_name for index, column_name in enumerate(next(reader))]
    list_output = []
    for rows in reader:
        list_output.append(dict(zip(column_index_to_name_map, rows)))
    return list_output

class FilterModule(object):
    def filters(self):
        return {
            'from_csv': csv_to_dict
        }
