# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         basic.py
# Purpose:      Basic retrosheet game record parsing
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
Basic retrosheet record types.  Everything except play and roster/substitution entries.
'''
from daseki.exceptionsDS import RetrosheetException
from daseki.retro.datatypeBase import RetroData


class Id(RetroData):
    '''
    defines the ID for the game
    '''
    __slots__ = ('id',)

    record = 'id'

    def __init__(self, retroId, *, parent=None):
        super().__init__(parent=parent)
        self.id = retroId

    def __repr__(self):
        return f'<{self.__module__}.{self.__class__.__name__} {self.id}>'


class Version(RetroData):
    '''
    defines the retrosheet version
    '''
    __slots__ = ('version',)

    record = 'version'

    def __init__(self, version=1, *, parent=None):
        super().__init__(parent=parent)
        self.version = version

    def __repr__(self):
        return f'<{self.__module__}.{self.__class__.__name__} {self.version}>'


class Adjustment(RetroData):
    '''
    for when a player bats or pitches with the opposite hand or player bats out of order
    '''
    __slots__ = ('playerId', 'hand')

    def __init__(self, playerId, hand=None, parent=None):
        super().__init__(parent=parent)
        self.playerId = playerId
        self.hand = hand

    def __repr__(self):
        return (f'<{self.__module__}.{self.__class__.__name__} ' 
                f'{self.playerId}: {self.hand}>')



class BattingAdjustment(Adjustment):
    record = 'badj'
    __slots__ = ()

    def __init__(self, playerId, hand=None, parent=None):
        super().__init__(playerId, hand, parent=parent)


class PitchingAdjustment(Adjustment):
    '''
    to date has happened once, Greg Harris, 9-28-1995

    Will have more evidence of this in 2015 data
    '''
    record = 'padj'
    __slots__ = ()

    def __init__(self, playerId, hand=None, *, parent=None):
        super().__init__(playerId, hand, parent=parent)


class OutOfOrderAdjustment(Adjustment):
    '''
    TO-DO: need example of this
    '''
    record = 'ladj'

    __slots__ = ()

    def __init__(self, playerId, hand=None, *,  parent=None):  # is hand necessary here?
        super().__init__(playerId, hand, parent=parent)




class RunnerAdjustment(RetroData):
    '''
    Used in games beginning in 2020 in which an extra inning begins with a runner on 2nd.
    '''
    record = 'radj'

    __slots__ = ('playerId', 'base')

    def __init__(self, playerId, base: int = 2, *, parent=None):
        super().__init__(parent=parent)
        self.playerId = playerId
        self.base = base

    def __repr__(self):
        return (f'<{self.__module__}.{self.__class__.__name__} ' 
                f'{self.playerId}: {self.base}>')


class PitcherResponsibilityAdjustment(RetroData):
    '''
    Not currently accounted for in stats.  Mostly occurred before 1940: the
    "wrong" pitcher is held responsible for a batter.

    PlayerId is the player who will get responsibility for the next play,
    and base is the number of the base of the runner that the pitcher is
    said to be responsible for.

    See https://www.retrosheet.org/presadj.htm
    '''
    record = 'presadj'

    __slots__ = ('playerId', 'base')

    def __init__(self, playerId, base: int|None = None, *, parent=None):
        super().__init__(parent=parent)
        self.playerId = playerId
        self.base = base

    def __repr__(self):
        return (f'<{self.__module__}.{self.__class__.__name__} ' 
                f'{self.playerId}: {self.base}>')


class Data(RetroData):
    '''
    At present, only earned runs data is generated
    '''
    __slots__ = ('dataType', 'playerId', 'runs')

    record = 'data'

    def __init__(self, dataType, playerId, runs, *, parent=None):
        super().__init__(parent=parent)
        if dataType != 'er':
            raise RetrosheetException(
                f'data other than earned runs encountered: {dataType} !'
            )
        self.dataType = dataType
        self.playerId = playerId
        self.runs = runs

    def __repr__(self):
        return '<%s.%s EarnedRuns, %s:%s>' % (self.__module__,
                                              self.__class__.__name__,
                                              self.playerId,
                                              self.runs)


class Comment(RetroData):
    '''
    Records a single comment entry
    '''
    __slots__ = ('comment',)
    record = 'com'

    def __init__(self, comment, *, parent=None):
        super().__init__(parent=parent)
        self.comment = comment

    def __repr__(self):
        return f'<{self.__module__}.{self.__class__.__name__} {self.comment}>'


class Info(RetroData):
    '''
    Defines a single retrosheet info record
    '''
    __slots__ = ('recordType', 'dataInfo')
    record = 'info'

    # htbf -- home team batted first!
    # https://github.com/natlownes/retrosheet_api_gae
    _gameRelatedTypes = (
            'visteam hometeam date number '
            'starttime daynight usedh pitches umphome ump1b ump2b ump3b umplf umprf '
            'fieldcond precip sky temp winddir windspeed timeofgame attendance site '
            'wp lp save gwrbi htbf oscorer gametype innings tiebreaker'
        )
    # gametype added in 2023 -- regular is the default
    # innings added in 2020 -- number of innings scheduled to play, if not 9.
    #    pandemic doubleheaders in 2020 were scheduled for 7 innings each.
    # tiebreaker added in 2020 -- will extra innings begin with a man on second?
    gameRelatedTypes = _gameRelatedTypes.split()
    _administrativeTypes = (
        'edittime howscored inputprogvers '
        'inputter inputtime scorer translator'
    )
    administrativeTypes = _administrativeTypes.split()
    knownTypes = gameRelatedTypes + administrativeTypes
    del _gameRelatedTypes
    del _administrativeTypes
    intTypes = 'number temp windspeed timeofgame attendance'.split()

    def __init__(self, recordType, dataInfo, *, parent=None):
        super().__init__(parent=parent)
        self.recordType = recordType
        if recordType not in self.knownTypes:
            raise RetrosheetException(f'Unknown record type {recordType!r} for info record')
        # if len(dataInfo) > 1:
        #    raise RetrosheetException('should only have one entry for dataInfo, not %r' % dataInfo)

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
            try:
                di = int(di)
            except ValueError:
                # Uncomment the next line after known errors are merged into Retrosheet.
                # print('Error to fix: ', recordType, self.parentByClass('Game'))
                di = 0

        self.dataInfo = di

    def __repr__(self):
        # return self.__class__.__name__
        return '<%s.%s %s:%s>' % (self.__module__,
                                  self.__class__.__name__,
                                  self.recordType,
                                  self.dataInfo)

if __name__ == '__main__':
    import daseki
    daseki.mainTest()
