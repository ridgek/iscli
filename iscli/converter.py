import re


VARIABLE_RE = re.compile(r'([A-Z]+)')
RANGE_RE = re.compile(r'<(\d+)\-(\d+)>')


def variable_converter(spec):
    m = VARIABLE_RE.match(spec)
    if m:
        return lambda arg: (True, arg)


def range_converter(spec):
    m = RANGE_RE.match(spec)
    if m:
        start, end = int(m.group(1)), int(m.group(2))

        def check(arg):
            try:
                value = int(arg)
                return (value >= start and value <= end, value)
            except ValueError:
                return (False, None)
        return check


def create_converter(spec):
    converters = (
        (VARIABLE_RE, variable_converter),
        (RANGE_RE, range_converter),
    )
    for regexp, fn in converters:
        if regexp.match(spec):
            return fn(spec)
