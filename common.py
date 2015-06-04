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
from __future__ import print_function
from __future__ import division

import os
# tools for setup.py
def sourceFilePath():
    '''
    Get the music21 directory that contains source files. This is not the same as the
    outermost package development directory.
    '''
    import bbbalk # pylint: disable=redefined-outer-name
    fpBalk = bbbalk.__path__[0] # list, get first item 
    # use corpus as a test case
    if 'retro' not in os.listdir(fpBalk):
        raise Exception('cannot find expected bbbalk directory: %s' % fpBalk)
    return fpBalk

def dataFilePath():
    return os.path.join(sourceFilePath(), 'dataFiles')

def dataDirByYear(year=2014):
    return os.path.join(dataFilePath(), str(year)) + 'eve'

if __name__ == '__main__':
    print(dataDirByYear(2012))
