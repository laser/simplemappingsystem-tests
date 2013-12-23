def dict_get(d, key, default=None):
    if d and d.has_key(key):
        return d[key]
    else:
        return default
