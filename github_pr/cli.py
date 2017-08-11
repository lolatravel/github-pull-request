import re
import os
import click
from termcolor import colored
from git import Repo
from pr import PR


ALIASES = {
    'ls': 'list'
}
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def get_remote_info(remote):
    owner = None
    repository = None
    match = re.search('^(http[s]?\:\/\/|git@)github.com(\/|\:)([^/]+)\/([^/]+)(?:.git)', remote.url)
    if match and len(match.groups()) == 4:
        owner = match.group(3)
        repository = match.group(4)
    return owner, repository


def get_github_token():
    return os.environ.get('GIT_PR_GITHUB_TOKEN')


def print_pull(pull):
    approved = '{0:5}'.format('\xE2\x9C\x94') if pull.approved else '{0:3}'.format('')
    line = colored('#{0:<6}'.format(pull.number), 'yellow')
    line += colored(approved, 'green' if pull.mergeable else 'magenta')
    line += colored('{0:8}'.format(pull.state), 'blue')
    line += colored('{0:20}'.format(pull.user), 'green')
    line += colored('{0}'.format(pull.title))
    click.echo(line)


class AliasedGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        elif ALIASES.get(cmd_name):
            return click.Group.get_command(self, ctx, ALIASES[cmd_name])
        else:
            ctx.fail('Unknown command: {0}'.format(cmd_name))

    def invoke(self, ctx):
        try:
            super(AliasedGroup, self).invoke(ctx)
        except Exception as e:
            click.echo('{0}: {1}'.format(e.__class__.__name__, e))
            raise click.Abort()


@click.command(
    cls=AliasedGroup,
    invoke_without_command=True,
    context_settings=CONTEXT_SETTINGS)
@click.option(
    '--remote',
    default='origin',
    metavar='<github remote>',
    help='Name of the origin to use, must be a GitHub repo')
@click.pass_context
def pr(ctx, remote):
    """
    CLI tool to manage GitHub PRs
    """
    repo = Repo('.')
    remote = repo.remote(remote)
    owner, repository = get_remote_info(remote)
    github_token = get_github_token()
    ctx.obj.client = PR(owner, repository, github_token)
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_prs)


@pr.command('list')
@click.pass_context
def list_prs(ctx):
    client = ctx.obj.client
    for pull in client.list():
        print_pull(pull)


@pr.command('get')
@click.argument('number', type=click.types.INT)
@click.option('--files', is_flag=True)
@click.option('--commits', is_flag=True)
@click.pass_context
def get_pr(ctx, number, files, commits):
    client = ctx.obj.client
    pull = client.get(number)
    print_pull(pull)
    if files:
        click.echo('\n Files:')
        for f in pull.files:
            click.echo(colored('{0:4}{1}'.format('', f.name), 'green'))
    if commits:
        click.echo('\n Commits:')
        for c in pull.commits:
            line = colored('{0:4}{1:8}'.format('', c.sha[:7]), 'yellow')
            line += colored(c.message, 'blue')
            click.echo(line)


@pr.command('merge')
@click.argument('number', type=click.types.INT)
@click.pass_context
def merge_pr(ctx, number):
    client = ctx.obj.client
    merge_sha = client.merge(number)
    click.echo('#{0} merged: {1}'.format(number, merge_sha))


def cli():
    class data(object):
        pass
    pr(obj=data())
