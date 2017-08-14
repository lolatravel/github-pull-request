from github import Github, GithubException
from utils import namedtype


Pull = namedtype('Pull', 'number, title, message, state, mergeable, user, approved, commits, files')
Commit = namedtype('Commit', 'sha, user, message')
File = namedtype('File', 'name')


class PR(object):

    def __init__(self, owner, repo, auth_token):
        self._github = Github(auth_token)
        self._repo = self._github.get_repo('{0}/{1}'.format(owner, repo))

    def _check_approved(self, pull):
        reviews = pull.get_reviews()
        return reduce(lambda a, r: a or r.state == 'APPROVED', reviews, False)

    def list(self, state='open', check_approved=True):
        pulls = self._repo.get_pulls(state=state)
        return [Pull(number=p.number, title=p.title, message=p.body, state=p.state,
                     user=p.user.name, mergeable=p.mergeable,
                     approved=self._check_approved(p) if check_approved else None) for p in pulls]

    def get(self, number, list_commits=True, list_files=True, check_approved=True):
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
