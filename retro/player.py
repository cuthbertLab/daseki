HOME = 1
VISITOR = 0

import weakref


from bbbalk.exceptionsBB import RetrosheetException
from bbbalk.retro.datatypeBase import RetroData

class Player(RetroData):
    '''
    a player.  It has information such as:
    
    .id -- playerId
    .name -- name
    .visitOrHome -- 0 = visitor, 1 = home
    .visitName -- "visitor" or "home"
    .battingOrder -- 
    '''
    _positionNames = "unknown pitcher catcher firstbase secondbase " + \
        "thirdbase shortstop leftfield centerfield rightfield " + \
        "designatedhitter pinchhitter pinchrunner"
    positionNames = _positionNames.split()
    visitorNames = ["visitor", "home"]
    del(_positionNames)
    
    def __init__(self, playerId, playerName, visitOrHome, battingOrder, position, parent=None):
        super(Player, self).__init__(parent=parent)
        try:
            self.id = playerId
            self.name = playerName
            self.visitOrHome = int(visitOrHome) # 0 = visitor, 1 = home
            self.visitName = self.visitorNames[int(visitOrHome)]
            self.battingOrder = battingOrder
            if position.endswith('"'): # parse error in 1996KCA.EVA and 1996MON.EVN
                position = position[0:len(position)-1]
            self.position = int(position)
            self.positionName = self.positionNames[int(position)]    
        except ValueError:
            raise RetrosheetException("Parse something for player %s " % playerName)

    def __repr__(self):
        return "<%s.%s %s,%s: %s (%s):%s>" % (self.__module__, self.__class__.__name__, 
                                  self.visitName, self.battingOrder, 
                                  self.name, self.id, self.positionName)


class Start(Player):
    record = 'start'
    
    def __init__(self, playerId, playerName, visitOrHome, battingOrder, position, parent=None):
        super(Start, self).__init__(playerId, playerName, visitOrHome, battingOrder, position, parent=parent)

class Sub(Player):
    record = 'sub'
    def __init__(self, playerId, playerName, visitOrHome, battingOrder, position, parent=None):
        super(Sub, self).__init__(playerId, playerName, visitOrHome, battingOrder, position, parent=parent)
    
    