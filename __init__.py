# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         __init__.py
# Purpose:      Daseki -- A toolkit for computational baseball analysis 
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2014-16 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
#------------------------------------------------------------------------------
'''
Daseki is a toolkit for computational baseball analysis, developed by
Michael Scott Cuthbert (Associate Prof. MIT).

Copyright 2014-16 Michael Scott Cuthbert / cuthbertLab
'''
__all__ = ['ext', 
           'retro', 
           
           'core',
           'common',
           'exceptionsDS', 
           'game',
           'player',
           'team'
           ]
__version_info__ = (0, 6, 0)
__version__ = '.'.join(str(x) for x in __version_info__)
__VERSION__ = __version__

from daseki import core
from daseki.test.testRunner import mainTest # @UnresolvedImport
from daseki.core import *

#------------------------------------------------------------------------------
# this bring all of the __all__ names into the bbbalk package namespace
from bbbalk import * # @UnresolvedImport
