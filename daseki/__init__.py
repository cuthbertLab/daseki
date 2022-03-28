# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         __init__.py
# Purpose:      Daseki -- A toolkit for computational baseball analysis
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2014-22 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
Daseki is a toolkit for computational baseball analysis, developed by
Michael Scott Cuthbert (Associate Prof. MIT).

Copyright 2014-17 Michael Scott Cuthbert / cuthbertLab
'''
__all__ = [
    'dwcompat',
    'common',
    'retro',

    'core',
    'exceptionsDS',
    'game',
    'player',
    'team',
    'test',

    'mainTest',
]
__version_info__ = (0, 6, 0)
__version__ = '.'.join(str(x) for x in __version_info__)
__VERSION__ = __version__

from sys import version_info as _pyver
if _pyver[0] <= 2 or (_pyver[0] == 3 and _pyver[1] <= 5):
    raise ImportError('Daseki requires Python 3.6 or higher. Exiting.')

from daseki import core
from daseki.test.testRunner import mainTest
from daseki.core import *

# -----------------------------------------------------------------------------
# this brings all of the __all__ names into the daseki package namespace
from daseki import dwcompat
from daseki import common
from daseki import retro
from daseki import exceptionsDS
from daseki import game
from daseki import player
from daseki import team
from daseki import test
