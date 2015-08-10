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
from bbbalk import common


class RetroData(common.ParentType):
    __slots__ = ('associatedComment', 'playNumber', '_parent')
    
    record = 'unknown'
    def __init__(self, parent=None):
        super(RetroData, self).__init__(parent)
        self.associatedComment = None
        self.playNumber = -1 # -1 = unknown
        # playNumber is the number of the play in the game (counting home and visitor)
        # for a play record, it indicates the last play record to occur.
        # for a sub it indicates the play record after which it occurred.
