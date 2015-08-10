# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         __init__.py
# Purpose:      BBBalk -- A toolkit for computational baseball analysis 
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2014-15 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
#------------------------------------------------------------------------------
'''
BBBalk is a toolkit for computational baseball analysis, developed by
Michael Scott Cuthbert (Associate Prof. MIT).

The title comes from baseball, obviously, and balk, as in what you should
expect traditional baseball heads to do when you present the results you
get from these objects.
'''
__all__ = ['ext', 
           'retro', 
           
           'base', 
           'common',
           'exceptionsBB', 
           'games',
           'player',
           ]
__version_info__ = (0, 5, 0)
__version__ = '.'.join(str(x) for x in __version_info__)
__VERSION__ = __version__

from bbbalk import base
from bbbalk.test.testRunner import mainTest # @UnresolvedImport
from bbbalk.base import *

#------------------------------------------------------------------------------
# this bring all of the __all__ names into the bbbalk package namespace
from bbbalk import * # @UnresolvedImport
