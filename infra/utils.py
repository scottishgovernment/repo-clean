#!/usr/bin/env python3.5

import datetime
import re


def version_compare(v1, v2):
    # TODO: DRY: original in ../../fabfile.py
    # Warning: this version is python3-compliant, the original is not
    # because of the use of the now-removed 'cmp' builtin function.

    def split_epoch(v):
        split = v.split(':', 1)
        if len(split) == 1:
            return (0, v)
        else:
            return tuple(split)

    def to_segment(v):
        if not v.isdigit():
            return v
        return int(v)

    def split_segments(v):
        return [to_segment(x) for x in re.split('[\.~-]', v)]

    def normalize(v):
        (epoch, version) = split_epoch(v)
        segments = split_segments(version)
        return (epoch, segments)

    # Python 2 only
    # return cmp(normalize(v1), normalize(v2))

    # Python 3 removed the builtin function 'cmp'
    a = normalize(v1)
    b = normalize(v2)
    # as suggested by https://docs.python.org/3.0/whatsnew/3.0.html
    return (a > b) - (a < b)


def is_earlier_version(a, b):
    """Return True if a is earlier version than b, else False

    >>> is_earlier_version('1.0.1', '1.0.2')
    True
    >>> is_earlier_version('1.0.1', '1.0.1')
    False
    >>> is_earlier_version('1.0.2', '1.0.1')
    False
    >>> is_earlier_version('2.8.2-2trusty', '2.8.3-4xenial')
    True
    >>> is_earlier_version('2017.05', '2015.08')
    False
    """
    return (version_compare(a, b) == -1)


def python_date_from_javascript_timestamp(javascript_timestamp):
    unix_timestamp = javascript_timestamp / 1000
    build_date = datetime.datetime.fromtimestamp(unix_timestamp)
    return build_date.date()


if __name__ == "__main__":
    import doctest
    doctest.testmod()

# eof
