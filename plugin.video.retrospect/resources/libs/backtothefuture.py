import sys

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    unichr = chr
    unicode = str
    basestring = str
else:
    import __builtin__
    unichr = __builtin__.unichr
    unicode = __builtin__.unicode
    basestring = __builtin__.basestring