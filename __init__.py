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
__ALL__ = ['base', 'retro', 'games', 'testRunner', 'exceptionsBB']
__VERSION__ = '0.2.0'

from bbbalk import base
from bbbalk.base import *
