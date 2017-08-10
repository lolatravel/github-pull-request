from github import Github
from utils import namedtype


Pull = namedtype('Pull', 'number, title, state, user, approved, commits, files')
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
        return [Pull(number=p.number, title=p.title, state=p.state, user=p.user.name,
                     approved=self._check_approved(p) if check_approved else None) for p in pulls]

    def get(self, number, list_commits=True, list_files=True, check_approved=True):
        p = self._repo.get_pull(number)
        commits = None
        if list_commits:
            commits = [Commit(sha=c.sha, user=c.author.name, message=c.commit.message) for c in p.get_commits()]

        files = None
        if list_files:
            files = [File(name=f.filename) for f in p.get_files()]

        return Pull(number=p.number, title=p.title, state=p.state, user=p.user.name,
                    approved=self._check_approved(p) if check_approved else None,
                    commits=commits, files=files)
