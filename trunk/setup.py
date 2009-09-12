#!/usr/bin/env python
from distutils.core import setup
from fooling import __version__

setup(
  name='fooling',
  version=__version__,
  license='MIT/X',
  author='Yusuke Shinyama',
  author_email='yusuke at cs dot nyu dot edu',
  url='http://www.unixuser.org/~euske/python/fooling/index.html',
  packages=[
    'fooling'
  ],
  scripts=[
    'tools/idxdump.py'
    'tools/idxmake.py'
    'tools/idxmerge.py'
    'tools/idxsearch.py'
    ],
  )
