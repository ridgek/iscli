from iscli.cli import CommandSet, Cli
from iscli.exceptions import ExitLoop


commands = CommandSet()
enable_commands = CommandSet()
conf_commands = CommandSet()


@commands.install('enable')
def cmd_enable(cli, args):
    cli.enable_mode.commandloop()
    cli.init_linenoise()


@enable_commands.install('disable')
def cmd_disable(cli, args):
    raise ExitLoop()


@enable_commands.install('show system')
def cmd_show_system(cli, args):
    print 'System OK'


@enable_commands.install('configure terminal')
def cmd_configure_terminal(cli, args):
    cli.conf_mode.commandloop()
    cli.init_linenoise()


@enable_commands.install('exit')
@conf_commands.install('exit')
@conf_commands.install('end')
def cmd_exit(cli, args):
    raise ExitLoop()


@conf_commands.install('hello world')
def cmd_hello_world(cli, args):
    print 'Hello World!'


if __name__ == '__main__':
    cli = Cli('>')
    cli.load(commands)
    enable_cli = cli.enable_mode = Cli('#')
    enable_cli.load(enable_commands)
    conf_cli = enable_cli.conf_mode = Cli('(conf)#')
    conf_cli.load(conf_commands)
    cli.commandloop()
