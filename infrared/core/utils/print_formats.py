from terminaltables import SingleTable


# TODO(aopincar): Highlight table header
def fancy_table(table_headers, *table_rows):
    """Creates a fancy table string from the given data

    :param table_headers: Iterable contains the table's headers
    :param table_rows: Iterable elements contain the table rows (body)
    :return: Formatted string represents the newly created table
    """
    table_data = [table_headers]
    table_data.extend(table_rows)

    table = SingleTable(table_data=table_data)
    table.inner_row_border = True

    return table.table
