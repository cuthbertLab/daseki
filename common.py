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
    Get the BBBalk directory that contains source files. This is not the same as the
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

ordinals = ["Zeroth","First","Second","Third","Fourth","Fifth",
            "Sixth","Seventh","Eighth","Ninth","Tenth","Eleventh",
            "Twelfth","Thirteenth","Fourteenth","Fifteenth",
            "Sixteenth","Seventeenth","Eighteenth","Nineteenth",
            "Twentieth","Twenty-first","Twenty-second"]

def ordinalAbbreviation(value, plural=False):
    '''Return the ordinal abbreviations for integers

    >>> from music21 import common
    >>> common.ordinalAbbreviation(3)
    'rd'
    >>> common.ordinalAbbreviation(255)
    'th'
    >>> common.ordinalAbbreviation(255, plural=True)
    'ths'

    :rtype: str
    '''
    valueHundreths = value % 100
    if valueHundreths in [11, 12, 13]:
        post = 'th'
    else:
        valueMod = value % 10
        if valueMod == 1:
            post = 'st'
        elif valueMod in [0, 4, 5, 6, 7, 8, 9]:
            post = 'th'
        elif valueMod == 2:
            post = 'nd'
        elif valueMod == 3:
            post = 'rd'

    if post != 'st' and plural:
        post += 's'
    return post



if __name__ == '__main__':
    print(dataDirByYear(2012))
