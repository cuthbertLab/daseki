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
    __slots__ = ('associatedComment', '_parent')
    
    record = 'unknown'
    def __init__(self, parent=None):
        super(RetroData, self).__init__(parent)
        self.associatedComment = None
