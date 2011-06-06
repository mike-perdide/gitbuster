from argparse import ArgumentParser
from os import makedirs, path, waitpid
from shutil import rmtree
from subprocess import Popen
from warnings import warn
import sys

DESCRIPTION = """This script generates a repository where cherry-picking
the last commit of the tmp branch from the master branch will cause a merge
conflict with every possible state of conflict represented:
 * AA on Z
 * AU on Y
 * UA on X
 * UU on jimmy
 * DU on toto
 * UD on tata
 * DD on foo"""

DEFAULT_TARGET = "/tmp/pathological_git_repo"


def run_cmd(command, directory=None):
    """
    command: tuple of words
    """
    echoable_cmd = " ".join(command)

    print "running > %s" % echoable_cmd
    kwargs = {'cwd': directory} if directory else {}
    process = Popen(command, **kwargs)
    status = waitpid(process.pid, 0)[1]
    assert status == 0, "Oops, something went wrong when running '%s'" % echoable_cmd


if __name__ == '__main__':
    parser = ArgumentParser(
        description = DESCRIPTION
        )
    parser.add_argument("--target", "-t", default=DEFAULT_TARGET)
    parser.add_argument("--erase", "-e", default=False, action='store_true',
        help="Delete target directory if it exists",
        )
    args = parser.parse_args()
    target = args.target

    if path.exists(target):
        if not args.erase:
            warn("Target (%s) exists. Not erasing it (or use --erase)"
                % target
            )
            sys.exit(2)
        rmtree(target)

    def git(*git_cmd):
        run_cmd(('git',) + git_cmd, directory=target)

    def fill_file(filename, content):
        with open(path.join(target, filename), 'w') as fdesc:
            fdesc.write(content)

    def git_add(filename):
        git('add', filename)

    makedirs(target)
    git('init')
    fill_file('foo', 'foo blabla\n')
    git_add('foo')
    fill_file('tata', 'tata blabla\n')
    git_add('tata')
    fill_file('jimmy', 'initial input\n')
    git_add('jimmy')
    git("commit", "-m", 'initial commit')

    git("checkout", "-b", "wallace_branch")

    fill_file("toto", "toto blabla\n")
    git_add("toto")
    git('commit', '-m', 'adding toto')

    git("mv", "foo", "X")
    fill_file("toto", "tata bloblo\n")
    git("rm", "tata")
    fill_file("Z", "Z tmp blabla\n")
    git_add("Z")
    fill_file("jimmy", "tmp input blabla\n")
    explanation = """conflictable commit

    rename foo to X, change the content of toto, remove tata, add Z,
    change the content of jimmy (rebase me to master)"""
    git("commit", "-a", "-m", explanation)

    git("checkout", "-")
    git("mv", "foo", "Y")
    git("commit", "-m", 'rename foo to Y')

    fill_file("Z", "Z blabla\n")
    git_add("Z")
    git("commit", "-m", 'adding Z')

    fill_file("tata", "other tata blabla\n")
    git("commit", "-a", "-m", 'changing the content of tata')

    fill_file("jimmy", "master input blabla\n")
    git("commit", "-a", "-m", 'changing the content of jimmy')
