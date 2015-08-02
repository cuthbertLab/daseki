# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         basic.py
# Purpose:      Basic retrosheet game record parsing
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
#------------------------------------------------------------------------------
'''
Basic retrosheet record types.  Everything except play and roster/substitution entries.
'''

import weakref

from bbbalk.exceptionsBB import RetrosheetException
from bbbalk.retro.datatypeBase import RetroData

class Id(RetroData):
    '''
    defines the ID for the game
    '''
    __slots__ = ('id')
    
    record = 'id'
    def __init__(self, parent, retroId):
        super(Id, self).__init__()
        self.parent = weakref.ref(parent)
        self.id = retroId

    def __repr__(self):
        return "<%s.%s %s>" % (self.__module__, self.__class__.__name__, self.id)

class Version(RetroData):
    '''
    defines the retrosheet version
    '''
    __slots__ = ('version')
    
    record = 'version'
    def __init__(self, parent, version=1):
        super(Version, self).__init__()
        self.parent = weakref.ref(parent)
        self.version = version

    def __repr__(self):
        return "<%s.%s %s>" % (self.__module__, self.__class__.__name__, self.version)


class Adjustment(RetroData):
    '''
    for when a player bats or pitches with the opposite hand or player bats out of order
    '''
    __slots__ = ('playerId', 'hand')
    
    def __init__(self, parent, playerId, hand=None):
        super(Adjustment, self).__init__()
        self.parent = weakref.ref(parent)
        self.playerId = playerId
        self.hand = hand

    def __repr__(self):
        return "<%s.%s %s: %s>" % (self.__module__, self.__class__.__name__, self.playerId, self.hand)

        

class BattingAdjustment(Adjustment):
    record = 'badj'
    def __init__(self, parent, playerId, hand=None):
        super(BattingAdjustment, self).__init__(parent, playerId, hand)

class PitchingAdjustment(Adjustment):
    '''
    to date has happened once, Greg Harris, 9-28-1995
    
    Will have more evidence of this in 2015 data
    '''
    record = 'padj'
    def __init__(self, parent, playerId, hand=None):
        super(PitchingAdjustment, self).__init__(parent, playerId, hand)

class OutOfOrderAdjustment(Adjustment):
    '''
    TO-DO: need example of this
    '''
    record = 'ladj'
    def __init__(self, parent, playerId, hand=None): # is hand necessary here?
        super(OutOfOrderAdjustment, self).__init__(parent, playerId, hand)

class Data(RetroData):
    '''
    At present, only er (earned runs) data is generated
    '''
    __slots__ = ('dataType', 'playerId', 'runs')
    
    record = 'data'
    def __init__(self, parent, dataType, playerId, runs):
        super(Data, self).__init__()
        self.parent = weakref.ref(parent)
        if dataType != 'er':
            raise RetrosheetException("data other than earned runs encountered: %s !" % dataType)
        self.dataType = dataType
        self.playerId = playerId
        self.runs = runs

    def __repr__(self):
        return "<%s.%s EarnedRuns, %s:%s>" % (self.__module__, self.__class__.__name__, self.playerId, self.runs)


class Comment(RetroData):
    '''
    Records a single comment entry
    '''
    __slots__ = ('comment')
    record = 'com'
    def __init__(self, parent, comment, *junk):
        super(Comment, self).__init__()
        self.parent = weakref.ref(parent)
        self.comment = comment
        # a very few comments such as 2006MIN.EVA have extra information after the , 
        # com,puntn001,R -- seems to be a miscoded badj

    def __repr__(self):
        return "<%s.%s %s>" % (self.__module__, self.__class__.__name__, self.comment)


class Info(RetroData):
    '''
    Defines a single retrosheet info record
    '''
    
    __slots__ = ('recordType', 'dataInfo')
    record = 'info'
    _gameRelatedTypes = "visteam hometeam date number " + \
        "starttime daynight usedh pitches umphome ump1b ump2b ump3b umplf umprf " + \
        "fieldcond precip sky temp winddir windspeed timeofgame attendance site " + \
        "wp lp save gwrbi htbf"  # htbf -- home team batted first! https://github.com/natlownes/retrosheet_api_gae
    gameRelatedTypes = _gameRelatedTypes.split()
    _administrativeTypes = "edittime howscored inputprogvers " + \
        "inputter inputtime scorer translator"
    administrativeTypes = _administrativeTypes.split()
    knownTypes = gameRelatedTypes + administrativeTypes
    del(_gameRelatedTypes)
    del(_administrativeTypes)
    
    def __init__(self, parent, recordType, *dataInfo):
        super(Info, self).__init__()
        self.parent = weakref.ref(parent)
        self.recordType = recordType
        if recordType not in self.knownTypes:
            raise RetrosheetException("Unknown record type %s for info record" % recordType)
        if len(dataInfo) > 1:
            raise RetrosheetException("should only have one entry for dataInfo, not %r" % dataInfo)
        self.dataInfo = dataInfo[0] 

    def __repr__(self):
        return "<%s.%s %s:%s>" % (self.__module__, self.__class__.__name__, self.recordType, self.dataInfo)

