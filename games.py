# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         games.py
# Purpose:      Represents Games and GameCollections
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
#------------------------------------------------------------------------------
from __future__ import division
from __future__ import print_function

DEBUG = False

import datetime
import unittest

from bbbalk.retro import basic, play, parser
from bbbalk import common
from bbbalk import base
from bbbalk import player # @UnresolvedImport
from bbbalk import team # @UnresolvedImport
from bbbalk.common import TeamNum

from collections import namedtuple
Runs = namedtuple('Runs', 'visitor home')
LeftOnBase = namedtuple('LeftOnBase', 'visitor home')

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
    _DOC_ATTR = {'park': '''
    A three letter abbreviation of the home team's park to play in.
    
    >>> gc = games.GameCollection()
    >>> gc.park = 'SDN'
    >>> gc.park
    'SDN'
    '''}
    def __init__(self):
        self.games = []
        self.yearStart = 2014
        self.yearEnd = 2014
        self.team = None
        self.park = None
        self.usesDH = None
        self.protoGames = []
        self.seasonType = 'regular'
        
    def addMatchingProtoGames(self):
        for y in range(self.yearStart, self.yearEnd + 1):
            yd = parser.YearDirectory(y, seasonType=self.seasonType)
            pgs = []
            if self.team is not None:
                pgs = yd.byTeam(self.team)
            elif self.park is not None:
                pgs = yd.byPark(self.park)
            elif self.usesDH is not None:
                pgs = yd.byUsesDH(self.usesDH)
            else:
                pgs = yd.all()
            self.protoGames.extend(pgs)
        return self.protoGames
        
    def parse(self):
        '''
        Parse all the files in the year range, filtered by team or park
        '''
        #print("Parsing {0}".format(self.yearStart))
        if len(self.protoGames) == 0:
            self.addMatchingProtoGames()
        
        errors = []
        for pg in self.protoGames:
            g = Game(parent=self)
            errors += g.mergeProto(pg, finalize=True)
            self.games.append(g)
        return self.games


class Game(common.ParentType):
    '''
    A Game records information about a game.
    
    Each game record is held somewhere in the `.records` list.
    Each half-inning is stored in the halfInnings list.
    '''
    @common.keyword_only_args('parent')
    def __init__(self, gameId=None, parent=None):
        super(Game, self).__init__(parent=parent)
        self.id = gameId
        self.records = []
        self._hasDH = None
        self.lineupHome = player.LineupCard(TeamNum.HOME, parent=self)
        self.lineupVisitor = player.LineupCard(TeamNum.VISITOR, parent=self)
        self.lineupCards = {TeamNum.HOME: self.lineupHome,
                            TeamNum.VISITOR: self.lineupVisitor}
        self.halfInnings = []
        if gameId is not None:
            self.parseFromId()

    def __repr__(self):
        return "<%s.%s %s>" % (self.__module__, self.__class__.__name__, 
                                  self.id)

    def parseFromId(self):
        '''
        Given the id set in self.id, find the appropriate ProtoGame and parse it into this
        Game object

        Not an efficient way of doing this for many games. But useful for looking at one.
        
        Returns a list of errors in parsing (hopefully empty)
        
        >>> g = games.Game()
        >>> g.id = 'SDN201304090'
        >>> g.parseFromId()
        []
        >>> g.runs
        Runs(visitor=3, home=9)
        '''
        pg = parser.protoGameById(self.id)
        return self.mergeProto(pg, finalize=True)


    def halfInningByNumber(self, number, visitOrHome):
        '''
        Return the HalfInning object associated with a given inning and visitOrHome
        
        >>> g = games.Game('SDN201304090')
        >>> hi = g.halfInningByNumber(7, common.TeamNum.VISITOR)
        >>> hi
        <bbbalk.base.HalfInning t7 plays:58-64 (SDN201304090)>
        '''
        for hi in self.halfInnings:
            if hi.inningNumber == number and hi.visitOrHome == visitOrHome:
                return hi
        return None

    def subByNumber(self, pn):
        '''
        Returns the sub (not play, etc.) that has a given number.  If none exists, returns None
        
        >>> g = games.Game('SDN201304090')
        >>> g.subByNumber(75)
        <bbbalk.player.Sub home,3: Tyson Ross (rosst001):pinchrunner>
        '''
        for hi in self.halfInnings:
            if hi.startPlayNumber <= pn and hi.endPlayNumber >= pn:
                return hi.subByNumber(pn) 
        return None

    def playByNumber(self, pn):
        '''
        Returns the play (not sub, etc.) that has a given number.  If none exists, returns None
        
        >>> g = games.Game('SDN201304090')
        >>> g.playByNumber(2)
        <bbbalk.retro.play.Play t1: kempm001:K>
        '''
        for hi in self.halfInnings:
            if hi.startPlayNumber <= pn and hi.endPlayNumber >= pn:
                return hi.playByNumber(pn) 
        return None


    def playerById(self, playerId):
        '''
        Returns the PlayerGame object representing a playerId in this game in either of the
        lineup cards:
        
        >>> g = games.Game('SDN201304090')
        >>> g.playerById('gyorj001')
        <bbbalk.player.PlayerGame home,5: Jedd Gyorko (gyorj001):[5]>
        '''
        for lc in self.lineupCards.values():
            p = lc.playerById(playerId)
            if p is not None:
                return p

    @property
    def numInnings(self):
        '''
        returns the traditional number of innings for the game as an int.
        
        I.e., a game that ends after T9 because the home team is ahead is still a 9 inning game.
        
        >>> g = games.Game('SDN201304090')
        >>> g.numInnings
        9
        '''
        nia2 = 2 * self.numInningsActual
        if nia2 % 2 == 1:
            nia2 += 1
        return int(nia2 / 2)
        
    @property
    def numInningsActual(self):
        '''
        returns the actual number of innings for the game as a float.
        
        I.e., a game that ends after T9 because the home team is ahead is an 8.5 inning game.

        >>> g = games.Game('SDN201304090')
        >>> g.numInningsActual
        8.5
        
        '''
        return len(self.halfInnings)/2.0

    @property
    def leftOnBase(self):
        '''
        returns a named tuple of (visitor, home) for the total number
        of runners left on base.
        
        >>> g = games.Game('SDN201403300')
        >>> g.leftOnBase
        LeftOnBase(visitor=6, home=6)
        '''
        lob = {TeamNum.VISITOR: 0, TeamNum.HOME: 0}
        for hi in self.halfInnings:
            lob[hi.visitOrHome] += hi.leftOnBase
        return LeftOnBase(lob[TeamNum.VISITOR], lob[TeamNum.HOME])

    def mergeProto(self, protoGame, finalize=True):
        '''
        The mergeProto function takes a ProtoGame object and loads all of these records into the
        records list as event objects.
        
        Returns a list of errors (hopefully empty)
        '''
        self.id = protoGame.id
        errors = []
        for d in protoGame.records:
            eventType = d[0]
            eventData = d[1:]
            eventClass = eventsToClasses[eventType]
            #common.warn(eventClass)
            try:
                rec = eventClass(*eventData, parent=self)
                self.records.append(rec)
            except TypeError as e:
                err = "Event Error in {0}: {1}: {2}".format(protoGame.id, str(e), str(d))
                common.warn(err) 
                errors.append(err)
        if finalize is True:
            self.finalizeParsing()
        return errors


    def finalizeParsing(self):
        lastInning = 0
        lastVisitOrHome = TeamNum.HOME
        lastRunners = base.BaseRunners(False, False, False)
        thisHalfInning = None
        halfInnings = []
        playNumber = -1
        for r in self.recordsByType(('play','sub', 'start')):
            if r.record in ('start', 'sub'):
                r.playNumber = playNumber # should be -1 for starters
                lc = self.lineupCards[r.visitOrHome]

                if r.record == 'sub':
                    #check for pinch runner
                    # cannot use lc.subsFor() during parsing.
                    subbedForPlayer = lc.playersByBattingOrder[r.battingOrder][-1]
                    for i, runOnBase in enumerate(lastRunners):
                        if runOnBase == subbedForPlayer.id:
                            lastRunners[i] = r.id
                        
                lc.add(r)
                r.inning = lastInning
            elif r.record == 'play':
                playNumber += 1
                r.playNumber = playNumber
                if r.inning != lastInning or r.visitOrHome != lastVisitOrHome: # new half-inning
                    if DEBUG:
                        common.warn("*** " + self.id + " Inning: " + str(r.inning) + " " + str(r.visitOrHome))
                    if thisHalfInning != None:
                        halfInnings.append(thisHalfInning)
                    lastHalfInning = thisHalfInning
                    thisHalfInning = base.HalfInning(parent=self)
                    if lastHalfInning is not None:
                        lastHalfInning.following = thisHalfInning
                        thisHalfInning.prev = lastHalfInning # None is okay here.
                        lastHalfInning.endPlayNumber = playNumber - 1
                    thisHalfInning.inningNumber = r.inning
                    thisHalfInning.visitOrHome = common.TeamNum(r.visitOrHome)
                    thisHalfInning.startPlayNumber = playNumber
                    lastRunners = base.BaseRunners(False, False, False, parent=r)                
                    lastInning = r.inning
                    lastVisitOrHome = r.visitOrHome
                r.runnersBefore = lastRunners
                r.runnersBefore.parent = r
                r.getPlayEvent().parse() 
                r.getRunnerEvent().parse()
                lastRunners = r.runnersAfter.copy()
            else:
                raise Exception("should only have play and sub records.")
            if thisHalfInning is not None:
                thisHalfInning.endPlayNumber = playNumber
                thisHalfInning.append(r)
                
        if thisHalfInning != None:
            halfInnings.append(thisHalfInning)
        self.halfInnings = halfInnings

    @property
    def homeTeam(self):
        ht = self.infoByType('hometeam')
        return team.Team(ht, self.date)
            
    @property
    def visitingTeam(self):
        vt = self.infoByType('visteam')
        return team.Team(vt, self.date)

    @property
    def date(self):
        d = self.infoByType('date')
        return datetime.datetime.strptime(d, "%Y/%m/%d")

    @property
    def dayNight(self):
        return self.infoByType('daynight')

    
    @property
    def runs(self):
        visitorRuns = 0
        homeRuns = 0
        for hi in self.halfInnings:
            if hi.visitOrHome == TeamNum.VISITOR:
                visitorRuns += hi.runs
            else:
                homeRuns += hi.runs
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

class Test(unittest.TestCase):
    pass

    @classmethod
    def setUpClass(cls):
        gc = GameCollection()
        gc.yearStart = 2013
        gc.yearEnd = 2013
        gc.team = 'SDN'
        cls.games = gc.parse()
        
    def testLeadoffBatterLedInning(self):
        pass
#         for hi in g.halfInnings:
#             for p in hi:
#                 if p.record != 'play':
#                     continue
#                 # finish when we can get player by id.
    
    def testInningIteration(self):
        g1 = self.games[0]
        h1 = g1.halfInnings[0]
        from pprint import pprint as pp
        pp(h1.__dict__)
        pp(h1.following)
        pp(g1.halfInnings[1])
        while h1 is not None:
            print(h1.inningNumber, h1.visitOrHome, '-------------------')
            for x in h1:
                print(x)
            h1 = h1.following
    
    def test2013Pads(self):
        totalWrong = 0
        for i, g in enumerate(self.games):
            print(g.id, g.runs)
            totalWrong += testCheckSaneOuts(g)
        print(self.games[5].halfInnings[3].parentByClass('Game'))
        print(self.games[5].halfInnings[3][2].parentByClass('Game'))
        print(self.games[5].halfInnings[3][2].playEvent.parentByClass('Game'))
        print(totalWrong, len(self.games))

class TestSlow(unittest.TestCase):
    def testAllYears(self):
        import multiprocessing
        import concurrent.futures
        
        def runOne(y):
            gc = GameCollection()
            gc.yearStart = y
            gc.yearEnd = y
            gc.seasonType = 'regular'
            print("Parsing {0}".format(y))
            gc.parse()
            
        max_workers = multiprocessing.cpu_count() - 1 # @UndefinedVariable
        if max_workers == 0:
            max_workers = 1
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            yy = [y for y in range(2014, 1870, -1)]
            runPath = {executor.submit(runOne, y) : y for y in yy}
            for future in concurrent.futures.as_completed(runPath):
                f = runPath[future]
                try:
                    unused_data = future.result()
                except Exception as exc:
                    print('%r generated an exception: %s' % (f, exc))
                else:
                    print('%r succeeded' % (f))

if __name__ == '__main__':
    from bbbalk import mainTest
    mainTest() #Test # TestSlow

