from iscli.cli import CommandSet, Cli


hello = CommandSet()


@hello.install('hello world')
def cmd_hello_world(cli, args):
    print 'Hello World!'


if __name__ == '__main__':
    cli = Cli('> ')
    cli.load(hello)
    cli.commandloop()
