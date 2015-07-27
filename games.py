HOME = 1
VISITOR = 0

DEBUG = False

from bbbalk.retro import basic, play, player, parser

from collections import namedtuple
Runs = namedtuple('Runs', 'visitor home')
LineupCard = namedtuple('LineupCard', 'visitor home')

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
    a collection of Game objects, in some order...
    
    Set .yearStart, .yearEnd, .team, and .park before running `.parse()`
    to limit parsing.
    '''
    def __init__(self):
        self.games = []
        self.yearStart = 2014
        self.yearEnd = 2014
        self.team = None
        self.park = None
        
    def parse(self):
        '''
        Parse all the files in the year range, filtered by team or park
        '''
        for y in range(self.yearStart, self.yearEnd + 1):
            yd = parser.YearDirectory(y)
            pgs = []
            if self.team is not None:
                pgs = yd.byTeam(self.team)
            elif self.park is not None:
                pgs = yd.byPark(self.park)
            else:
                pgs = yd.all()
            for pg in pgs:
                g = Game()
                g.mergeProto(pg, finalize=True)
                self.games.append(g)
        return self.games


class Game(object):
    '''
    A Game records information about a game.
    
    Each game record is held somewhere in the `.records` list.
    Each half-inning is stored in the halfInnings list.
    '''
    def __init__(self, gameId=None):
        self.id = gameId
        self.records = []
        self._hasDH = None
        self._startersHome = []
        self._startersVisitor = []
        self.halfInnings = []

    def mergeProto(self, protoGame, finalize=True):
        '''
        The mergeProto function takes a ProtoGame object and loads all of these records into the
        .records list as event objects.
        '''
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
            elif r.record == 'play':
                if r.inning != lastInning or r.visitOrHome != lastVisitOrHome: # new half-inning
                    if DEBUG:
                        print("*** " + self.id + " Inning: " + str(r.inning) + " " + str(r.visitOrHome))
                    if thisHalfInning != None:
                        halfInnings.append(thisHalfInning)
                    thisHalfInning = []
                    lastRunners = [False, False, False]                
                    lastInning = r.inning
                    lastVisitOrHome = r.visitOrHome
                r.runnersBefore = lastRunners[:]
                r.playEvent # TODO -- this just forces parsing... should call explicitly...
                r.runnerEvent # TODO -- this just forces parsing...should call explicitly...
                lastRunners = r.runnersAfter[:]
            else:
                raise Exception("should only have play and sub records.")
            thisHalfInning.append(r)
                
        if thisHalfInning != None:
            halfInnings.append(thisHalfInning)
        self.halfInnings = halfInnings

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
        '''
        Finds the first info record to have a given info type
        
        
        '''
        for i in self.recordsByType('info'):
            if i.recordType == infotype:
                return i.dataInfo

    def recordsByType(self, recordTypeOrTypes):
        '''
        Iterates through all records which fits a single type or list of types, such as "play" or "info" etc.
        '''
        if isinstance(recordTypeOrTypes, (list, tuple)):
            for r in self.records:
                if r.record in recordTypeOrTypes:
                    yield r            
        else:
            for r in self.records:
                if r.record == recordTypeOrTypes:
                    yield r
                
    def hasDH(self):
        '''
        Returns True or False about whether the game used a designated hitter.
        '''
        if self._hasDH is not None:
            return self._hasDH
        useDH = self.infoByType('usedh')
        if useDH == 'true':
            self._hasDH = True
        else:
            self._hasDH = False
        return self._hasDH
        
    def starters(self):
        '''
        Gives the named tuple of two lists of starters for visitor and home.
        '''
        
        if self._startersHome != []:
            return LineupCard(visitor=self._startersVisitor, home=self._startersHome)

        for r in self.recordsByType('start'):
            if r.visitOrHome == HOME:
                self._startersHome.append(r)
            else:
                self._startersVisitor.append(r)
        return LineupCard(visitor=self._startersVisitor, home=self._startersHome)

def testCheckSaneOuts(g):
    from pprint import pprint as pp
    totalHalfInnings = len(g.halfInnings)
    wrong = 0
    for i, half in enumerate(g.halfInnings):
        outs = 0
        if i == totalHalfInnings - 1:
            continue
        for p in half:
            if p.record == 'play':
                outs += p.outsMadeOnPlay
        
        if outs != 3:
            print(g.id, outs)
            pp(half)
            wrong += 1
            for p in half:
                if p.record == 'play':
                    omop = p.outsMadeOnPlay
                    if omop > 0:
                        pp((p.outsMadeOnPlay, repr(p)))
    return wrong

def testLeadoffBatterLedInning(g):
    for hi in g.halfInnings:
        for p in hi:
            if p.record != 'play':
                continue
            # finish when we can get player by id.
            

if __name__ == '__main__':
    gc = GameCollection()
    gc.yearStart = 2000
    gc.yearEnd = 2014
    gc.team = 'SDN'
    games = gc.parse()
    totalWrong = 0
    for g in games:
        #print(g.id, g.runs)
        totalWrong += testCheckSaneOuts(g)
    print(totalWrong, len(games))

