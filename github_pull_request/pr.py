from github import Github, GithubException
from utils import namedtype

# Types
Pull = namedtype('Pull', 'number, title, message, state, mergeable, user, approved, commits, files')
Commit = namedtype('Commit', 'sha, user, message')
File = namedtype('File', 'name')


class PR(object):
    """
    Simple wrapper around GitHub's API for pul requests. Turns teh responses into simple
    objects for easier consumption and exposes simple methods for retrieving and merging
    PRs.
    """

    def __init__(self, owner, repo, auth_token):
        """
        @param owner       The GitHub user/organization name that owns the repo
        @param repo        The name of the GitHub repository
        @param auth_token  A GitHub auth token, usually a Personal Access Token

        Example:
            GitHub url: https://github.com/lolatravel/github-pull-request
            owner: lolatravel
            repo: github-pull-request
        """
        self._github = Github(auth_token)
        self._repo = self._github.get_repo('{0}/{1}'.format(owner, repo))

    def _check_approved(self, pull):
        """
        Retrieves and loops over all reviews and returns true if any review is approved.

        returns  True if any review was approved else False
        """
        reviews = pull.get_reviews()
        return reduce(lambda a, r: a or r.state == 'APPROVED', reviews, False)

    def list(self, state='open', check_approved=True):
        """
        List PRs

        @param state              Filter PRs by state, default 'open'
        @param check_approved     Check whether any reviews for this PR are approved

        returns   list of `Pull`s
        """
        pulls = self._repo.get_pulls(state=state)
        return [Pull(number=p.number, title=p.title, message=p.body, state=p.state,
                     user=p.user.name, mergeable=p.mergeable,
                     approved=self._check_approved(p) if check_approved else None) for p in pulls]

    def get(self, number, list_commits=True, list_files=True, check_approved=True):
        """
        Get a single PR and optional additional info.

        @param  number          PR number
        @param  list_commits    Retrieve the list of commits associated with this PR
        @param  list_files      Retrieve the list of files assocaited with this PR
        @param  check_approved  Check whether any reviews for this PR are approved

        returns  `Pull`
        """
        p = self._repo.get_pull(number)
        commits = None
        if list_commits:
            commits = [Commit(sha=c.sha, user=c.author.name, message=c.commit.message) for c in p.get_commits()]

        files = None
        if list_files:
            files = [File(name=f.filename) for f in p.get_files()]

        return Pull(number=p.number, title=p.title, message=p.body, state=p.state, user=p.user.name,
                    approved=self._check_approved(p) if check_approved else None,
                    mergeable=p.mergeable, commits=commits, files=files)

    def merge(self, number, message=None):
        """
        Merge this PR using `message` as the commit message for the merge commit. By default this
        method will use the PR title and body plus the list of commits and files as the commits message.
        This is nice so that the context of the PR is kept in the merge commit and can be referenced
        when viewing the history, git blame, etc.

        @param  message    String to use as the commit message if teh default is not sufficient

        returns  string, the sha of the merge commit
        """
        p = self._repo.get_pull(number)
        pull = self.get(number, list_commits=True, list_files=True, check_approved=False)
        if message is None:
            commits = ['  Commits:']
            for c in p.get_commits():
                msg = c.commit.message[:57] + '...' if len(c.commit.message) > 60 else c.commit.message
                commits.append('{0:4}{1:8} {2:20} {3}'.format('', c.sha[:7], '<' + c.author.name + '>', msg))

            files = ['  Files:']
            for f in p.get_files():
                files.append('{0:4}{1}'.format('', f.filename))

            message = '{0}\n\n{1}\n\n{2}\n\n{3}'.format(
                pull.title, pull.message, '\n'.join(commits), '\n'.join(files))

        try:
            merge = p.merge(commit_message=message)
        except GithubException as e:
            msg = 'Status: {0}'.format(e.status)
            if 'message' in e.data:
                msg += ': {0}'.format(e.data['message'])
            if 'documentation_url' in e.data:
                msg += '\n See: {0}'.format(e.data['documentation_url'])
            raise Exception(msg)

        return merge.sha
