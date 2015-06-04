HOME = 1
VISITOR = 0

DEBUG = False

from bbbalk.retro import basic, play, player, parser

from collections import namedtuple
Runs = namedtuple('Runs', 'visitor home')

eventsToClasses = {
                   'id': basic.Id,
                   'version': basic.Version,
                   'info': basic.Info,
                   'badj': basic.BattingAdjustment,
                   'padj': basic.PitchingAdjustment,
                   'ladj': basic.OutOfOrderAdjustment,
                   'data': basic.Data,
                   'com': basic.Comment,
                   'start': player.Start,
                   'sub': player.Sub,
                   'play': play.Play,
                   }

class GameCollection(object):
    '''
    a collection of games, in some order...
    '''
    def __init__(self):
        self.games = []
        self.yearStart = 2014
        self.yearEnd = 2014
        self.team = None
        self.park = None
        
    def parse(self):
        for y in range(self.yearStart, self.yearEnd + 1):
            yd = parser.YearDirectory(y)
            pgs = []
            if self.team is not None:
                pgs = yd.byTeam(self.team)
            elif self.park is not None:
                pgs = yd.byPark(self.park)
            else:
                pgs = yd.protoGames
            for pg in pgs:
                g = Game()
                g.mergeProto(pg)
                self.games.append(g)
        return self.games


class Game(object):
    '''
    records information about a game.
    '''
    def __init__(self, gameId=None):
        self.id = gameId
        self.records = []
        self._hasDH = None
        self._startersHome = []
        self._startersVisitor = []
        self.halfInnings = []

    def mergeProto(self, protoGame, finalize=True):
        self.id = protoGame.id
        for d in protoGame.records:
            eventType = d[0]
            eventData = d[1:]
            eventClass = eventsToClasses[eventType]
            rec = eventClass(self, *eventData)
            self.records.append(rec)
        if finalize is True:
            self.finalizeParsing()

    def finalizeParsing(self):
        lastInning = 0
        lastVisitOrHome = HOME
        # pinch runner!
        lastRunners = [False, False, False]
        thisHalfInning = None
        halfInnings = []
        for r in self.recordsByType(('play','sub')):
            if r.record == 'sub':
                if DEBUG:
                    print("@#%&^$*# SUB")
            else:
                if r.inning != lastInning or r.visitOrHome != lastVisitOrHome:
                    if DEBUG:
                        print("*** " + self.id + " Inning: " + str(r.inning) + " " + str(r.visitOrHome))
                    if thisHalfInning != None:
                        halfInnings.append(thisHalfInning)
                    thisHalfInning = []
                    lastRunners = [False, False, False]                
                    lastInning = r.inning
                    lastVisitOrHome = r.visitOrHome            
                r.runnersBefore = lastRunners
                r.playEvent
                r.runnerEvent
                lastRunners = r.runnersAfter
                thisHalfInning.append(r)
                
        if thisHalfInning != None:
            halfInnings.append(thisHalfInning)

    @property
    def homeTeam(self):
        return self.infoByType('hometeam')
    
    @property
    def visitingTeam(self):
        return self.infoByType('visteam')
    
    @property
    def runs(self):
        visitorRuns = 0
        homeRuns = 0
        for p in self.recordsByType('play'):
            if p.visitOrHome == VISITOR:
                visitorRuns += p.runnerEvent.runs
            else:
                homeRuns += p.runnerEvent.runs
        return Runs(visitorRuns, homeRuns)
    

    def infoByType(self, infotype):
        for i in self.recordsByType('info'):
            if i.recordType == infotype:
                return i.dataInfo

    def recordsByType(self, recordTypeOrTypes):
        if isinstance(recordTypeOrTypes, (list, tuple)):
            for r in self.records:
                if r.record in recordTypeOrTypes:
                    yield r            
        else:
            for r in self.records:
                if r.record == recordTypeOrTypes:
                    yield r
                
    def hasDH(self):
        if self._hasDH is not None:
            return self._hasDH
        useDH = self.infoByType('usedh')
        if useDH == 'true':
            self._hasDH = True
        else:
            self._hasDH = False
        return self._hasDH
        
    def starters(self, whichOne = HOME):
        if whichOne == HOME and self._startersHome != []:
            return self._startersHome
        elif whichOne == VISITOR and self._startersVisitor != []:
            return self._startersVisitor
        for r in self.recordsByType('start'):
            if r.visitOrHome == HOME:
                self._startersHome.append(r)
            else:
                self._startersVisitor.append(r)
        if whichOne == HOME:
            return self._startersHome
        else:
            return self._startersVisitor


if __name__ == '__main__':
    gc = GameCollection()
    gc.yearStart = 2013
    gc.yearEnd = 2014
    gc.team = 'SDN'
    games = gc.parse()
    for g in games:
        print(g.id, g.runs)
