import sys
from colorclass import Color

if (hasattr(sys.stdout, "isatty") and sys.stdout.isatty()):
    # we use Unicode based tables only on interactive console
    from terminaltables import SingleTable as NiceTable
else:
    # Jenkins console works with coloring but not with Unicode based tables
    from terminaltables import AsciiTable as NiceTable


def fancy_table(table_headers, *table_rows):
    """Creates a fancy table string from the given data

    :param table_headers: Iterable contains the table's headers
    :param table_rows: Iterable elements contain the table rows (body)
    :return: Formatted string represents the newly created table
    """
    # coloring class degrates gracefully if output is redirected so we will
    # not endup with ANSI escapes if we redirect console.
    table_data = [[Color('{autoblue}%s{/autoblue}' % c)
                   for c in table_headers]]
    table_data.extend(table_rows)

    table = NiceTable(table_data=table_data)
    table.inner_row_border = True

    return table.table
