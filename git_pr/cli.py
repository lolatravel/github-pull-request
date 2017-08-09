import click


ALIASES = {
    'ls': 'list'
}


class AliasedGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        elif ALIASES.get(cmd_name):
            return click.Group.get_command(self, ctx, ALIASES[cmd_name])
        else:
            ctx.fail('Unknown command: {0}'.format(cmd_name))


@click.command(cls=AliasedGroup)
def pr():
    """CLI tool to manage GitHub PRs"""
    pass


@pr.command()
def list():
    click.echo('Listing...')
    click.echo('done')
