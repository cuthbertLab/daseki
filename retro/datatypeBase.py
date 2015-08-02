# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         dataTypeBase.py
# Purpose:      dataTypeBase -- Base Class to override
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
#------------------------------------------------------------------------------
import weakref
from bbbalk import common

class ParentType(common.SlottedObject):
    __slots__ = ('_parent')
    
    def __init__(self, parent=None):
        self._parent = None
        self.parent = parent

    def _getParent(self):
        if type(self._parent) is weakref.ref:
            return self._parent()
        else:
            return self._parent
        
    def _setParent(self, referent):
        try:
            self._parent = weakref.ref(referent)
        # if referent is None, will raise a TypeError
        # if referent is a weakref, will also raise a TypeError
        # will also raise a type error for string, ints, etc.
        # slight performance bost rather than checking if None
        except TypeError:
            self._parent = referent
    
    parent = property(_getParent, _setParent)

class RetroData(ParentType):
    
    __slots__ = ('associatedComment')

    
    record = 'unknown'
    def __init__(self, parent=None):
        super(RetroData, self).__init__(parent)
        self.associatedComment = None
