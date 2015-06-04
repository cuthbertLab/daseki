HOME = 1
VISITOR = 0

import weakref


from bbbalk.exceptionsBB import RetrosheetException
from bbbalk.retro.datatypeBase import RetroData


class Player(RetroData):
    '''
    a player
    '''
    _positionNames = "unknown pitcher catcher firstbase secondbase " + \
        "thirdbase shortstop leftfield centerfield rightfield " + \
        "designatedhitter pinchhitter pinchrunner"
    positionNames = _positionNames.split()
    visitorNames = ["visitor", "home"]
    del(_positionNames)
    
    def __init__(self, parent, playerId, playerName, visitOrHome, battingOrder, position):
        self.parent = weakref.ref(parent)
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


class Start(Player):
    record = 'start'

class Sub(Player):
    record = 'sub'