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
from daseki import common
from daseki.exceptionsBB import RetrosheetException
from daseki.retro.datatypeBase import RetroData

class Id(RetroData):
    '''
    defines the ID for the game
    '''
    __slots__ = ('id',)
    
    record = 'id'
    #@common.keyword_only_args('parent')
    def __init__(self, retroId, parent=None):
        super(Id, self).__init__(parent=parent)
        self.id = retroId

    def __repr__(self):
        return "<%s.%s %s>" % (self.__module__, self.__class__.__name__, self.id)

class Version(RetroData):
    '''
    defines the retrosheet version
    '''
    __slots__ = ('version',)
    
    record = 'version'
    #@common.keyword_only_args('parent')
    def __init__(self, version=1, parent=None):
        super(Version, self).__init__(parent=parent)
        self.version = version

    def __repr__(self):
        return "<%s.%s %s>" % (self.__module__, self.__class__.__name__, self.version)


class Adjustment(RetroData):
    '''
    for when a player bats or pitches with the opposite hand or player bats out of order
    '''
    __slots__ = ('playerId', 'hand')
    
    #@common.keyword_only_args('parent')
    def __init__(self, playerId, hand=None, parent=None):
        super(Adjustment, self).__init__(parent=parent)
        self.playerId = playerId
        self.hand = hand

    def __repr__(self):
        return "<%s.%s %s: %s>" % (self.__module__, self.__class__.__name__, self.playerId, self.hand)

        

class BattingAdjustment(Adjustment):
    record = 'badj'
    __slots__ = ()
    #@common.keyword_only_args('parent')
    def __init__(self, playerId, hand=None, parent=None):
        super(BattingAdjustment, self).__init__(playerId, hand, parent=parent)

class PitchingAdjustment(Adjustment):
    '''
    to date has happened once, Greg Harris, 9-28-1995
    
    Will have more evidence of this in 2015 data
    '''
    record = 'padj'
    __slots__ = ()

    #@common.keyword_only_args('parent')
    def __init__(self, playerId, hand=None, parent=None):
        super(PitchingAdjustment, self).__init__(playerId, hand, parent=parent)

class OutOfOrderAdjustment(Adjustment):
    '''
    TO-DO: need example of this
    '''
    record = 'ladj'
    
    __slots__ = ()
    #@common.keyword_only_args('parent')
    def __init__(self, playerId, hand=None, parent=None): # is hand necessary here?
        super(OutOfOrderAdjustment, self).__init__(playerId, hand, parent=parent)

class Data(RetroData):
    '''
    At present, only er (earned runs) data is generated
    '''
    __slots__ = ('dataType', 'playerId', 'runs')
    
    record = 'data'
    #@common.keyword_only_args('parent')
    def __init__(self, dataType, playerId, runs, parent=None):
        super(Data, self).__init__(parent=parent)
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
    __slots__ = ('comment',)
    record = 'com'
    #@common.keyword_only_args('parent')
    def __init__(self, comment, parent=None):
        super(Comment, self).__init__(parent=parent)
        self.comment = comment

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
    intTypes = "number temp windspeed timeofgame attendance".split()
    
    #@common.keyword_only_args('parent')
    def __init__(self, recordType, dataInfo, parent=None):
        super(Info, self).__init__(parent=parent)
        self.recordType = recordType
        if recordType not in self.knownTypes:
            raise RetrosheetException("Unknown record type %s for info record" % recordType)
        #if len(dataInfo) > 1:
        #    raise RetrosheetException("should only have one entry for dataInfo, not %r" % dataInfo)
    
        di = dataInfo
        if di == 'unknown':
            di = None
            
        if recordType == 'windspeed' and di == '-1':
            di = None
        elif recordType == 'temp' and di == '0':
            di = None
        elif recordType == 'starttime' and di == '0:00':
            di = None
            
        if di is not None and recordType in self.intTypes:
            di = int(di)
        
        
        self.dataInfo = di 

    def __repr__(self):
        return self.__class__.__name__
        return "<%s.%s %s:%s>" % (self.__module__, self.__class__.__name__, self.recordType, self.dataInfo)

if __name__ == '__main__':
    import daseki
    daseki.mainTest()
