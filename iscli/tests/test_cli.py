# -*- coding: utf-8 -*-

from StringIO import StringIO

from nose.tools import assert_in, assert_not_in

from iscli.cli import Cli


test_cli = Cli()


DESC_SHOW = 'Show running system information'
DESC_SHOW_SYSTEM = 'System properties'


@test_cli.install(
    'show system',
    [DESC_SHOW,
     DESC_SHOW_SYSTEM]
)
def _cmd_show_system(cli, args):
    cli.out('System ok')


@test_cli.install(
    'show version',
    [DESC_SHOW,
     'Software version']
)
def _cmd_show_version(cli, args):
    """System version"""
    cli.out('Version 1.0')


@test_cli.install(
    'test range <1-10>',
    ['Test command',
     'Test range',
     'number']
)
def _cmd_test_range(cli, args):
    cli.out('test range')


@test_cli.install(
    'test opt (bar|)',
    ['Test command',
     'Test optional',
     'Bar']
)
def _cmd_test_opt(cli, args):
    cli.out('test opt')


@test_cli.install(
    'test vararg .WORD',
    ['Test command',
     'Test vararg',
     'argument']
)
def _cmd_test_vararg(cli, args):
    cli.out('test vararg')


@test_cli.install(
    ('sshfs HOSTNAME username USERNAME ({path PATH | port <1-65535>}|)'),
    ['Manage ATMF feature',
     'A.B.C.D, X:X::X:X or host name',
     'SSH Username',
     'Username',
     'Remote path',
     'Path',
     'SSH Port',
     'Port']
)
def _cmd_sshfs_mount(cli, args):
    cli.out('sshfs mount')


class TestCli(object):
    def capture(self):
        test_cli.stdout = StringIO()
        return test_cli.stdout

    def describe(self, cmd):
        cap = self.capture()
        test_cli.describe(cmd)
        return cap.getvalue()

    def command(self, cmd):
        cap = self.capture()
        test_cli.command(cmd)
        return cap.getvalue()

    def test_describe(self):
        out = self.describe('')
        assert_in('show', out)
        assert_in(DESC_SHOW, out)
        assert_not_in('version', out)
        assert_in('Test command', out)

        out = self.describe('s')
        assert_in('show', out)
        assert_in('sshfs', out)
        assert_not_in('test', out)

        out = self.describe('sh')
        assert_in('show', out)
        assert_not_in('sshfs', out)

        out = self.describe('show ')
        assert_in('system', out)
        assert_in('version', out)
        assert_not_in('<cr>', out)

        out = self.describe('show s')
        assert_in('system', out)
        assert_not_in('version', out)
        assert_not_in('<cr>', out)

        out = self.describe('show путь')
        assert_not_in('<cr>', out)

    def test_command(self):
        for cmd in ['show system', 'show sys', 'sh sys']:
            assert_in('System ok', self.command(cmd))

        for cmd in ['show', 'sh', 'путь']:
            assert_in('Unrecognized', self.command(cmd))

        assert_in('Ambiguous', self.command('s'))

    def test_range(self):
        assert_in('Unrecognized', self.command('test range'))
        assert_in('<1-10>', self.describe('test range '))
        assert_not_in('<cr>', self.describe('test range '))

        for i in range(1, 10 + 1):
            assert_in('test range', self.command('test range %d' % i))
            assert_in('<cr>', self.describe('test range %d ' % i))

        for i in [-123, -10, -5, -1, 0, 11, 123]:
            assert_in('Unrecognized', self.command('test range %d' % i))

        assert_in('Unrecognized', self.command('test range 1 1'))

    def test_opt(self):
        assert_in('test opt', self.command('test opt'))
        assert_in('bar', self.describe('test opt '))
        assert_in('<cr>', self.describe('test opt '))

        assert_in('test opt', self.command('test opt bar'))
        assert_in('<cr>', self.describe('test opt bar '))

        assert_in('Unrecognized', self.command('test opt foo'))
        assert_in('Unrecognized', self.describe('test opt foo '))

        assert_in('Unrecognized', self.command('test opt bar foo'))

    def test_vararg(self):
        assert_in('Unrecognized', self.command('test vararg'))
        assert_in('WORD', self.describe('test vararg '))

        assert_in('test vararg', self.command('test vararg foo'))
        assert_in('WORD', self.describe('test vararg foo '))
        assert_in('<cr>', self.describe('test vararg foo '))

        assert_in('test vararg', self.command('test vararg foo bar'))
        assert_in('WORD', self.describe('test vararg foo bar '))
        assert_in('<cr>', self.describe('test vararg foo bar '))

        assert_in('test vararg', self.command('test vararg foo foo 6'))
        assert_in('WORD', self.describe('test vararg foo foo foo 6 '))
        assert_in('<cr>', self.describe('test vararg foo foo foo 6 '))

if __name__ == '__main__':
    test_cli.commandloop()
