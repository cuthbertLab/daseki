import weakref

from bbbalk.exceptionsBB import RetrosheetException
from bbbalk.retro.datatypeBase import RetroData

class Id(RetroData):
    '''
    defines the ID for the game
    '''
    record = 'id'
    def __init__(self, parent, retroId):
        self.parent = weakref.ref(parent)
        self.id = retroId

class Version(RetroData):
    '''
    defines the retrosheet version
    '''
    record = 'version'
    def __init__(self, parent, version=1):
        self.parent = weakref.ref(parent)
        self.version = version

class Adjustment(RetroData):
    '''
    for when a player bats or pitches with the opposite hand or player bats out of order
    '''
    def __init__(self, parent, playerId, hand=None):
        self.parent = weakref.ref(parent)
        self.playerId = playerId
        self.hand = hand

class BattingAdjustment(Adjustment):
    record = 'badj'

class PitchingAdjustment(Adjustment):
    '''
    to date has happened once, Greg Harris, 9-28-1995
    '''
    record = 'padj'

class OutOfOrderAdjustment(Adjustment):
    '''
    TO-DO: need example of this
    '''
    record = 'ladj'

class Data(RetroData):
    '''
    At present, only er (earned runs) data is generated
    '''
    record = 'data'
    def __init__(self, parent, dataType, playerId, runs):
        self.parent = weakref.ref(parent)
        if dataType != 'er':
            raise RetrosheetException("data other than earned runs encountered: %s !" % dataType)
        self.dataType = dataType
        self.playerId = playerId
        self.runs = runs

class Comment(RetroData):
    '''
    Records a single comment entry
    '''
    record = 'com'
    def __init__(self, parent, comment, *junk):
        self.parent = weakref.ref(parent)
        self.comment = comment
        # a very few comments such as 2006MIN.EVA have extra information after the , 
        # com,puntn001,R -- seems to be a miscoded badj

class Info(RetroData):
    '''
    Defines a single retrosheet info record
    '''
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
        self.parent = weakref.ref(parent)
        self.recordType = recordType
        if recordType not in self.knownTypes:
            raise RetrosheetException("Unknown record type %s for info record" % recordType)
        if len(dataInfo) > 1:
            raise RetrosheetException("should only have one entry for dataInfo, not %r" % dataInfo)
        self.dataInfo = dataInfo[0] 
