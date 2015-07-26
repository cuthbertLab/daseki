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
class RetroData(object):
    record = 'unknown'
    def __init__(self):
        self.associatedComment = None
