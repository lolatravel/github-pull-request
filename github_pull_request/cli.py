import re
import os
import webbrowser
import click
from termcolor import colored
from git import Repo
from pr import PR


# Map of aliased commands
ALIASES = {
    'ls': 'list'
}
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

remote_opt = click.option('--remote', default='origin', metavar='<github remote>', help='Name of the origin to use, must be a GitHub repo')
contains_opt = click.option('--contains', metavar='<commit SHA>', help='Show pull requests containing a particular commit')
files_opt = click.option('--files', is_flag=True, help='Flag to list files associated with the PR')
commits_opt = click.option('--commits', is_flag=True, help='Flag to list commits associated with the PR')
open_opt = click.option('--open', is_flag=True, help='Flag to open the PR in web browser')

def get_remote_info(remote):
    """
    Extract the GitHub user/organization and repo name from the remote url.
    """
    owner = None
    repository = None
    match = re.search('^(http[s]?\:\/\/|git@)github.com(\/|\:)([^/]+)\/([^/]+)(?:.git)', remote.url)
    if match and len(match.groups()) == 4:
        owner = match.group(3)
        repository = match.group(4)
    return owner, repository


def get_github_token():
    return os.environ.get('GITHUB_ACCESS_TOKEN')


def print_pull(pull):
    """
    Print a formatted and colored PR to the console.
    """
    approved = '{0:5}'.format('\xE2\x9C\x94') if pull.approved else '{0:3}'.format('')
    line = colored('#{0:<6}'.format(pull.number), 'yellow')
    line += colored(approved, 'green' if pull.mergeable else 'magenta')
    line += colored('{0:8}'.format(pull.state), 'blue')
    line += colored('{0:20}'.format(pull.user.name.encode('utf-8')), 'green')
    line += colored('{0}'.format(pull.title.encode('utf-8')))
    click.echo(line)


class AliasedGroup(click.Group):
    """
    This class handles checking the alias map and invoking the correct
    command if an entry is found.
    """

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
@remote_opt
@contains_opt
@open_opt
@click.pass_context
def pr(ctx, remote, contains, open):
    """
    CLI tool to manage GitHub PRs
    """
    repo = Repo('.')
    remote = repo.remote(remote)
    owner, repository = get_remote_info(remote)
    github_token = get_github_token()
    ctx.obj.client = PR(owner, repository, github_token)
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_prs, contains=contains, open=open)


@pr.command('list')
@contains_opt
@open_opt
@click.pass_context
def list_prs(ctx, contains, open):
    client = ctx.obj.client
    for pull in client.list(contains=contains):
        print_pull(pull)
        if open:
            webbrowser.open(pull.url)


@pr.command('get')
@click.argument('number', type=click.types.INT, metavar='<number>')
@files_opt
@commits_opt
@open_opt
@click.pass_context
def get_pr(ctx, number, files, commits, open):
    """
    Retrive info about PR number <number>, optionally including the list of files
    and commits associated with the PR.
    """
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
    if open:
        webbrowser.open(pull.url)


@pr.command('merge')
@click.argument('number', type=click.types.INT, metavar='<number>')
@click.pass_context
def merge_pr(ctx, number):
    """
    Merge PR number <number>. The default message for the merge commit will contain the body
    of the PR as well as the list of files and commits associated with the PR.
    """
    client = ctx.obj.client
    merge_sha = client.merge(number)
    click.echo('#{0} merged: {1}'.format(number, merge_sha))


def cli():
    class data(object):
        pass
    pr(obj=data())
