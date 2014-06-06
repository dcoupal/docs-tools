import logging
import os
import re
from contextlib import contextmanager

from giza.tools.shell import command

logger = logging.getLogger(os.path.basename(__file__))

class GitRepo(object):
    def __init__(self, path=None):
        if path is None:
            self.path = os.getcwd()
        else:
            self.path = path

        logger.debug("created git repository management object for {0}".format(self.path))

    def cmd(self, *args):
        args = ' '.join(args)

        return command(command='cd {0} ; git {1}'.format(self.path, args), capture=True)

    def remotes(self):
        return self.cmd('remote').out.split('\n')

    def branch_file(self, path, branch='master'):
        return self.cmd('show {branch}:{path}'.format(branch=branch, path=path)).out

    def checkout(self, ref):
        return self.cmd('checkout', ref)

    def hard_reset(self, ref='HEAD'):
        return self.cmd('reset', '--hard', ref)

    def reset(self, ref='HEAD'):
        return self.cmd('reset', ref)

    def fetch(self, remote='origin'):
        return self.cmd('fetch', remote)

    def update(self):
        return self.cmd('pull', '--rebase')

    def pull(self, remote='origin', branch='master'):
        return self.cmd('pull', remote, branch)

    def current_branch(self):
        return self.cmd('symbolic-ref', 'HEAD').out.split('/')[2]

    def sha(self, ref='HEAD'):
        return self.cmd('rev-parse', '--verify', ref).out

    def clone(self, remote, repo_path=None, branch=None):
        args = ['clone', remote]

        if branch is not None:
            args.extend(['--branch', branch])

        if repo_path is not None:
            args.append(repo_path)

        return self.cmd(*args)

    def cherry_pick(self, *args):
        for commit in args:
            self.cmd('cherry-pick', commit)

    def am(self, patches, repo=None, sign=False):
        cmd_base = 'curl {path} | git am --3way'

        if sign is True:
            cmd_base += ' --signoff'

        for obj in patches:
            if obj.startswith('http'):
                if not obj.endswith('.patch'):
                    obj += '.patch'

                self.cmd(cmd_base.format(path=obj))
                logger.info("applied {0}".format(obj))
            elif re.search('[a-zA-Z]+', obj):
                path = '/'.join([ repo, 'commit', obj ]) + '.patch'

                self.cmd(cmd_base.format(path=path))
                logger.info('merged commit {0} for {1} into {2}'.format(obj, repo, self.current_branch()))
            else:
                if repo is None:
                    logger.warning('not applying "{0}", because of missing repo'.format(obj))
                else:
                    path = '/'.join([ repo, 'pull', obj ]) + '.patch'
                    self.cmd(cmd_base.format(path=path))
                    logger.info("applied {0}".format(obj))

    @contextmanager
    def branch(self, name):
        starting_branch = self.current_branch

        if name != starting_branch:
            self.checkout(name)

        yield

        if name != starting_branch:
            self.checkout(starting_branch)