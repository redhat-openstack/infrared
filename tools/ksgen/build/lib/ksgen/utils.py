def extract_value(mapping, key, default=None, optional=True):

    # raise KeyError if it doesn't exist
    val = mapping[key] if not optional else None

    if key not in mapping:
        return default

    val = val or mapping[key]    # reuse val already set
    del mapping[key]
    return val

to_list = lambda x: x if isinstance(x, (list, tuple)) else [x]
