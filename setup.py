#!/usr/bin/env python
from setuptools import setup

setup(name='qGitFilterBranch',
      version='1.0',
      description='git filter-branch qt interface',
      author='Julien Miotte',
      author_email='miotte.julien@gmail.com',
      packages=['qGitFilterBranch'],
      requires=('GitPython (>0.3.0)',),
      license='GPLv3',
      entry_points={'console_scripts' : ['qGitFilterBranch = qGitFilterBranch:run']}
     )
