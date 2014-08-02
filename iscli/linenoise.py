"""
Bindings for linenoise line editing library
"""
import os
import cffi
import logging


ffi = cffi.FFI()

_root = os.path.abspath(os.path.dirname(__file__))
ffi.cdef('void free(void *ptr);')
with open(os.path.join(_root, 'linenoise_ffi.h')) as header:
    ffi.cdef(header.read())
del header

_c = ffi.verify(
    '#include "linenoise.h"',
    sources=[os.path.join(_root, 'linenoise.c')],
    extra_compile_args=['-I%s' % _root]
)

_callbacks = {
    'complete': None,
    'describe': None,
}

_logger = logging.getLogger('linenoise')
_logger.addHandler(logging.NullHandler())


@ffi.callback('void(const char *, const char *, linenoiseCompletions *)')
def _complete_cb(line, text, completions):
    try:
        line = ffi.string(line)
        text = ffi.string(text)
        _logger.info('complete: "%s" "%s"' % (line, text))
        complete = _callbacks['complete']
        for completion in complete(line, text):
            _logger.debug('completion: "%s"' % completion)
            _c.linenoiseAddCompletion(
                completions,
                ffi.new('char[]', completion)
            )
    except Exception:
        _logger.exception('Exception raised in complete callback')


@ffi.callback('void(const char *)')
def _describe_cb(line):
    try:
        line = ffi.string(line)
        _logger.info('describe: "%s"' % line)
        describe = _callbacks['describe']
        describe(line)
    except Exception:
        _logger.exception('Exception raised in describe callback')


def set_completion_callback(fn):
    """Set the completetion function
    Pass None to unset.

    complete(line) -> [..., ...]
    """
    _logger.info('set_completion_callback: %r' % fn)
    _callbacks['complete'] = fn
    _c.linenoiseSetCompletionCallback(_complete_cb if fn else ffi.NULL)


def set_describe_callback(fn):
    """Set the describe function.
    Pass None to unset.

    describe(line) -> None
    """
    _logger.info('set_describe_callback: %r' % fn)
    _callbacks['describe'] = fn
    _c.linenoiseSetDescribeCallback(_describe_cb if fn else ffi.NULL)


def linenoise(prompt):
    line = _c.linenoise(ffi.new('char[]', prompt))
    if line == ffi.NULL:
        raise EOFError
    try:
        return ffi.string(line)
    finally:
        _c.free(line)


def history_add(line):
    """Add a new entry in the linenoise history."""
    _logger.info('history_add: %r' % line)
    return _c.linenoiseHistoryAdd(ffi.new('char[]', line))


def history_set_max_len(length):
    """Set the maximum length for the history."""
    _logger.info('history_set_max_len: %d' % length)
    return _c.linenoiseHistorySetMaxLen(length)


def history_save(filename):
    """Save the history in the specified file."""
    _logger.info('history_save: %r' % filename)
    if _c.linenoiseHistorySave(ffi.new('char[]', filename)):
        _logger.error('failed to save history (%d)' % ffi.errno)
        raise OSError(ffi.errno, os.strerror(ffi.errno))


def history_load(filename):
    """Load the history from the specified file."""
    if _c.linenoiseHistoryLoad(ffi.new('char[]', filename)):
        _logger.error('failed to load history (%d)' % ffi.errno)
        raise OSError(ffi.errno, os.strerror(ffi.errno))


def clear_screen():
    """Clear the screen. Used to handle ctrl+l"""
    _logger.info('clear_screen')
    _c.linenoiseClearScreen()


def set_multi_line(ml):
    """Set if to use or not the multi line mode."""
    _logger.info('set_multi_line: %r' % ml)
    _c.linenoiseSetMultiLine(int(bool(ml)))


if __name__ == '__main__':
    def complete(line):
        a = []
        if 'foo'.startswith(line):
            a.append('foo')
        if 'foobar'.startswith(line):
            a.append('foobar')
        if 'bar'.startswith(line):
            a.append('bar')
        if 'baz'.startswith(line):
            a.append('baz')
        return a

    def describe(line):
        print 'No help here'

    set_completion_callback(complete)
    set_describe_callback(describe)

    while True:
        try:
            line = linenoise('hello> ')
        except EOFError:
            print 'Bye'
            break
        else:
            history_add(line)
            print 'echo: "%s"' % line
