from __future__ import print_function

import shlex
import sys

from .exceptions import ExitLoop
from .node import cmdsplit, make_root
from . import linenoise


class CommandSet(object):
    def __init__(self):
        self.commands = {}
        self._on_load = None

    def add(self, fn, cmdspec, desc, **options):
        self.commands[cmdspec] = ((fn, cmdspec, desc), options)

    def install(self, cmdspec, desc=None, **options):
        """A decorator to install a command into the CommandSet.

        :param cmdspec: command specification
        :param desc: sequence of help text
        """
        def decorator(fn):
            self.add(fn, cmdspec, desc, **options)
            return fn
        return decorator

    def on_load(self, fn):
        """A decorator to set a callback to be run when this CommandSet
        is loaded by a Cli

        The callback is passed one argument, the Cli object.
        """
        self._on_load = fn
        return fn

    def load_into(self, cli):
        """Load this CommandSet into a Cli."""
        for args, options in self.commands.itervalues():
            cli.register(*args, **options)

        if self._on_load:
            self._on_load(cli)


class Cli(object):
    def __init__(self, prompt='>', command_sets=None):
        self.root = make_root()
        self.prompt = prompt

        self.stdout = sys.stdout

        for command_set in (command_sets or []):
            self.load(command_set)

    def out(self, *objects, **kwargs):
        kwargs['file'] = self.stdout
        return print(*objects, **kwargs)

    def load(self, command_set):
        """Load a CommandSet of commands into this Cli."""
        old_root = self.root
        try:
            command_set.load_into(self)
        except Exception:
            # Try recover the tree to a good state
            self.root = old_root
            raise

    def register(self, fn, cmdspec, desc, **options):
        """Register a command into this Cli.

        :param fn: function to register
        :param cmdspec: command specification
        :param desc: sequence of help text
        """
        root = make_root()
        elements = cmdsplit(cmdspec, desc)
        root.build(elements, fn)
        root.merge(self.root)
        self.root = root

    def expand(self, command, extra=False):
        """Expand a command into a dictionary of possible matches.

        :param command: command to expand
        :param extra: include next possible argument, useful for completion
        :type extra: bool
        :returns: dictionary where keys are expanded commands and the values
                  are :class:`tuple`s of :class:`CliNode`s.
        """
        exp_command = []
        node = self.root
        path = []
        for fragment in command:
            nodes = node.match(fragment)
            matches = len(nodes)
            if matches == 1:
                exp_fragment, node = nodes.popitem()
                path.append(node)
                exp_command.append(exp_fragment)
            elif matches > 1:
                # Ambiguous
                return {
                    tuple(exp_command + [k]): tuple(path + [n])
                    for k, n in nodes.iteritems()
                }
            else:
                # No matches
                return {}

        if extra:
            # Asked for next fragment
            commands = {
                tuple(exp_command + [k]): tuple(path + [n])
                for k, n in node.match('').iteritems()
            }
            if node.fn:
                commands[tuple(exp_command)] = tuple(path)
            return commands

        if exp_command:
            # Found an exact match
            return {tuple(exp_command): tuple(path)}

        return {}

    def complete(self, line, text):
        """Complete command

        :param line: line buffer
        :param text: word to complete
        :returns: list of possibile words
        """
        command = self.parse(line)
        if command:
            extra = not text.strip()
            i = len(command) - int(not extra)
            return sorted(set(
                n[i].keyword
                for n in self.expand(command, extra=extra).itervalues()
                if len(n) > i and n[i].element.converter is None
            ))
        return []

    def parse(self, line):
        """Parse a command line into a tuple of arguments."""
        return tuple(shlex.split(line.strip()))

    def emptyline(self):
        """Called when an empty line is entered"""
        pass

    def error_unrecognized(self, line):
        self.out('% Unrecognized command\n')

    def error_ambiguous(self, line):
        self.out('%% Ambiguous command: "%s"\n' % line)

    def describe(self, line):
        """Show contextual help

        :param line: line buffer

        Example::

            >use b?
              bar   Pour a drink
              broom Sweep the floor
        """
        extra = (line == '' or line[-1] == ' ')
        command = self.parse(line)
        commands = self.expand(command, extra=extra)
        if not commands:
            self.out(line)
            self.error_unrecognized(line)
            return

        if extra:
            # See if we can get an exact match
            exp_commands = self.expand(command)
            if exp_commands:
                command, _ = exp_commands.popitem()
                if exp_commands:
                    self.error_ambiguous(line)
                    return

        print_cr = False
        for c, nodes in sorted(commands.iteritems()):
            node = nodes[-1]
            if node.fn and extra and c == command:
                print_cr = True
                continue
            desc = node.element.desc
            self.out('  %s\t%s' % (c[-1], desc))

        if print_cr:
            self.out('  <cr>')
        self.out()

    def command(self, line):
        """Execute a command"""
        commands = self.expand(self.parse(line))
        matches = len(commands)
        if not matches:
            self.error_unrecognized(line)
        elif matches > 1:
            self.error_ambiguous(line)
        else:
            command, nodes = commands.popitem()
            node = nodes[-1]
            if node.fn:
                args = [
                    a
                    for a, n in zip(command, nodes)
                    if n.element.is_argument
                ]
                return node.fn(self, args)
            else:
                self.error_unrecognized(line)

    def init_line_editor(self):
        linenoise.set_describe_callback(self.describe)
        linenoise.set_completion_callback(self.complete)

    def commandloop(self):
        while True:
            self.init_line_editor()
            try:
                line = linenoise.linenoise(self.prompt).strip()
            except EOFError:
                break

            if not line:
                self.emptyline()
                continue

            if line[-1] == '?':
                self.describe(line.rstrip('?'))
                continue

            linenoise.history_add(line)
            try:
                self.command(line)
            except ExitLoop:
                break
