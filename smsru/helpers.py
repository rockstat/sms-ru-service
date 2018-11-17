"""
Library
"""
from time import time


def dictlist(dict_):
    """
    Convert dict to flat list
    """
    return [item for pair in dict_.items() for item in pair]


def pairs(l):
    """
    Convert list to pairs
    """
    for i in range(0, len(l), 2):
        # Create an index range for l of n items:
        yield (*l[i:i+2],)


def gen_key(uid, section='s'):
    """
    Generate store key for own user
    """
    return f'cs:{section}:{uid}'.encode()


def ms():
    return int(time() * 1000)
