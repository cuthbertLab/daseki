# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         game.py
# Purpose:      Represents Games and GameCollections
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------

DEBUG = False

import pickle
import datetime
import os
import unittest

from collections import namedtuple, OrderedDict
from pprint import pprint as pp

from daseki import common
from daseki import core
from daseki import player
from daseki import team
from daseki.common import TeamNum
from daseki.retro import basic, play, parser, protoGame
from daseki.exceptionsDS import GameParseException


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


class GameCollection():
    '''
    a collection of Game objects, in some order...

    Set .yearStart, .yearEnd, .team, and .park before running `.parse()`
    to limit parsing.
    '''
    _DOC_ATTR = {'park': '''
    A three letter abbreviation of the home team's park to play in.
    
    >>> gc = game.GameCollection()
    >>> gc.park = 'SDN'
    >>> gc.park
    'SDN'
    '''}

    def __init__(self, yearStart=2015, yearEnd=None, team=None):
        super().__init__()
        self.games = []
        self.yearStart = yearStart
        self.yearEnd = yearEnd or yearStart
        self.team = team
        self.park = None
        self.usesDH = None
        self.protoGames = []
        self.seasonType = 'regular'
        self.overrideDirectory = None

    def addMatchingProtoGames(self):
        for y in range(self.yearStart, self.yearEnd + 1):
            yd = parser.YearDirectory(y,
                                      seasonType=self.seasonType,)
            if self.overrideDirectory:
                yd.overrideDirectory = self.overrideDirectory
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

    def _pickleFN(self):
        # noinspection PyProtectedMember
        '''
        Return a pickle filename for the game collection.

        >>> from daseki import game
        >>> gc = game.GameCollection()
        >>> gc.yearStart = 1994
        >>> gc.yearEnd = 2000
        >>> gc.team = 'BOS'
        >>> gc.usesDH = True
        >>> gc._pickleFN()
        'gc19942000tBOSpdt0.6.0.p'
        '''
        import daseki
        teamFN = 't'
        if self.team is not None:
            teamFN += self.team
        park = 'p'
        if self.park is not None:
            park += self.park
        usesDH = 'd'
        if self.usesDH is True:
            usesDH += 't'
        elif self.usesDH is False:
            usesDH += 'f'

        hashFN = ('gc' + str(self.yearStart) + str(self.yearEnd) + teamFN + park +
                  usesDH + daseki.__version__ + '.p')
        return hashFN

    def save(self):
        pfn = os.path.join(common.getDefaultRootTempDir(), self._pickleFN())
        with open(pfn, 'wb') as pFileHandle:
            pickle.dump(self.games, pFileHandle, protocol=pickle.HIGHEST_PROTOCOL)


    def sortGames(self):
        '''
        Sort games by date then team.
        '''
        self.games.sort(key=lambda x: (int(x.id[3:]), x.id[0:3]))

    def parse(self):
        '''
        Parse all the files in the year range, filtered by team or park
        '''
        # Pickling only resulted in a 20% speedup for subsequent calls, but a 3x
        # slowdown for first call -- not worth it.  Oh, and one season was 792 MB!
        if len(self.protoGames) == 0:
            self.addMatchingProtoGames()

        # errors = []
        # pgIndices = list(range(len(self.protoGames)))
        # list(common.multicore(self._parseOne)(pgIndices))
        # return self.games

        for pg in self.protoGames:
            g = Game(parent=self)
            _unused_errors = g.mergeProto(pg)
            # pylint: disable=broad-except
            try:
                g.finalizeParsing()
            except Exception as exc:
                raise GameParseException(
                    f'Error in {g.id}: {str(exc)}'
                ) from exc

            self.games.append(g)
        self.sortGames()
        # if not forceSource:
        #     self.save()
        return self.games


class Game(common.ParentMixin):
    '''
    A Game records information about a game.

    Each game record is held somewhere in the `.records` list.
    Each half-inning is stored in the halfInnings list.
    '''
    __slots__ = ('id', 'records', 'lineupHome', 'lineupVisitor', 'lineupCards', 'halfInnings',)

    def __init__(self, gameId=None, *, parent=None):
        super().__init__(parent=parent)
        self.id = gameId
        self.records = []
        self.lineupHome = player.LineupCard(TeamNum.HOME, parent=self)
        self.lineupVisitor = player.LineupCard(TeamNum.VISITOR, parent=self)
        self.lineupCards = {TeamNum.HOME: self.lineupHome,
                            TeamNum.VISITOR: self.lineupVisitor}
        self.halfInnings = []
        if gameId is not None:
            self.parseFromId()

    def __repr__(self):
        return f'<{self.__module__}.{self.__class__.__name__} {self.id}>'

    def parseFromId(self):
        '''
        Given the id set in self.id, find the appropriate ProtoGame and parse it into this
        Game object

        Not an efficient way of doing this for many games. But useful for looking at one.

        Returns a list of errors in parsing (hopefully empty)

        >>> from daseki import game
        >>> g = game.Game()
        >>> g.id = 'SDN201304090'
        >>> g.parseFromId()
        []
        >>> g.runs
        Runs(visitor=3, home=9)
        '''
        pg = protoGame.protoGameById(self.id)
        errors = self.mergeProto(pg)
        self.finalizeParsing()
        return errors


    def halfInningByNumber(self, number, visitOrHome):
        '''
        Return the HalfInning object associated with a given inning and visitOrHome

        >>> from daseki import game
        >>> g = game.Game('SDN201304090')
        >>> hi = g.halfInningByNumber(7, common.TeamNum.VISITOR)
        >>> hi
        <daseki.core.HalfInning t7 plays:58-64 (SDN201304090)>
        '''
        for hi in self.halfInnings:
            if hi.inningNumber == number and hi.visitOrHome == visitOrHome:
                return hi
        return None

    def subByNumber(self, pn):
        '''
        Returns the sub (not play, etc.) that has a given number.  If none exists, returns None

        >>> from daseki import game
        >>> g = game.Game('SDN201304090')
        >>> g.subByNumber(75)
        <daseki.player.Sub home,3: Tyson Ross (rosst001):pinchrunner>
        '''
        for hi in self.halfInnings:
            if hi.startPlayNumber <= pn <= hi.endPlayNumber:
                return hi.subByNumber(pn)
        return None

    def playByNumber(self, pn):
        '''
        Returns the play (not sub, etc.) that has a given number.  If none exists, returns None

        >>> from daseki import game
        >>> g = game.Game('SDN201304090')
        >>> g.playByNumber(2)
        <daseki.retro.play.Play t1: kempm001:K>
        '''
        for hi in self.halfInnings:
            if hi.startPlayNumber <= pn <= hi.endPlayNumber:
                return hi.playByNumber(pn)
        return None


    def playerById(self, playerId):
        '''
        Returns the PlayerGame object representing a playerId in this game in either of the
        lineup cards:

        >>> from daseki import game
        >>> g = game.Game('SDN201304090')
        >>> g.playerById('gyorj001')
        <daseki.player.PlayerGame home,5: Jedd Gyorko (gyorj001):[5]>
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

        >>> from daseki import game
        >>> g = game.Game('SDN201304090')
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

        >>> from daseki import game
        >>> g = game.Game('SDN201304090')
        >>> g.numInningsActual
        8.5

        '''
        return len(self.halfInnings)/2.0

    @property
    def leftOnBase(self):
        '''
        returns a named tuple of (visitor, home) for the total number
        of runners left on base.

        >>> from daseki import game
        >>> g = game.Game('SDN201403300')
        >>> g.leftOnBase
        LeftOnBase(visitor=6, home=6)
        '''
        lob = {TeamNum.VISITOR: 0, TeamNum.HOME: 0}
        for hi in self.halfInnings:
            lob[hi.visitOrHome] += hi.leftOnBase
        return LeftOnBase(lob[TeamNum.VISITOR], lob[TeamNum.HOME])

    def mergeProto(self, protoGame):
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
            # common.warn(eventClass)
            try:
                rec = eventClass(*eventData, parent=self)
                self.records.append(rec)
            except (TypeError, ValueError) as e:
                err = 'Event Error in {0}: {1}: {2}'.format(protoGame.id, str(e), str(d))
                common.warn(err)
                errors.append(err)

        return errors

    def finalizeParsing(self):
        '''
        Given a set of record classes in self.record that have already been
        instantiated into objects, populate the lineupCards and
        halfInnings and also parse the play events.
        '''
        lastInning = 0
        lastVisitOrHome = TeamNum.HOME
        lastRunners = core.BaseRunners(False, False, False)
        thisHalfInning = None
        halfInnings = []
        playNumber = -1
        for r in self.recordsByType(('play', 'sub', 'start')):
            if r.record in ('start', 'sub'):
                r.playNumber = playNumber  # should be -1 for starters
                lc = self.lineupCards[r.visitOrHome]

                if r.record == 'sub':
                    # check for pinch runner
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
                if r.inning != lastInning or r.visitOrHome != lastVisitOrHome:  # new half-inning
                    if DEBUG:
                        common.warn('*** ' + self.id + ' Inning: ' + str(r.inning) +
                                    ' ' + str(r.visitOrHome))
                    if thisHalfInning is not None:
                        halfInnings.append(thisHalfInning)
                    lastHalfInning = thisHalfInning
                    thisHalfInning = core.HalfInning(parent=self)
                    if lastHalfInning is not None:
                        lastHalfInning.following = thisHalfInning
                        thisHalfInning.prev = lastHalfInning  # None is okay here.
                        lastHalfInning.endPlayNumber = playNumber - 1
                    thisHalfInning.inningNumber = r.inning
                    thisHalfInning.visitOrHome = common.TeamNum(r.visitOrHome)
                    thisHalfInning.startPlayNumber = playNumber
                    lastRunners = core.BaseRunners(False, False, False, parent=r)
                    lastInning = r.inning
                    lastVisitOrHome = r.visitOrHome
                r.runnersBefore = lastRunners
                r.runnersBefore.parent = r
                _unused = r.playEvent  # this will call Parse() on each, with good exception
                _unused = r.runnerEvent  # handling and caching
                lastRunners = r.runnersAfter.copy()
            else:
                raise GameParseException('should only have play and sub records.')
            if thisHalfInning is not None:
                thisHalfInning.endPlayNumber = playNumber
                thisHalfInning.append(r)

        if thisHalfInning is not None:
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
        return datetime.datetime.strptime(d, '%Y/%m/%d')

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


    def infoByType(self, infoType):
        '''
        Finds the first info record to have a given info type
        '''
        for i in self.recordsByType('info'):
            if i.recordType == infoType:
                return i.dataInfo

    def recordsByType(self, recordTypeOrTypes):
        '''
        Iterates through all records which fits a single type or list of types,
        such as "play" or "info" etc.
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
        useDH = self.infoByType('usedh')
        if useDH == 'true':
            hasDH = True
        else:
            hasDH = False
        return hasDH

    def battersByEvent(self, eventAttribute, visitOrHome=None):
        '''
        Returns an OrderedDict of batterIds whose playEvents have a
        certain attribute is True or an int > 0.

        The order is the order that the batter first made a play.  The value is the number of times
        the play was made.  For instance if eventAttribute == 'single'
        and gregg001 singled in the second
        and fourth, bobob001 singled in the third, and steve001 singled in the fifth, you'd get
        {'gregg001': 2, 'bobob001': 1, 'steve001': 1}

        If visitOrHome is set then only return plays where the batter is a member of that TeamNum.

        >>> from daseki import game
        >>> g = game.Game('SDN201304090')
        >>> g.battersByEvent('single')
        OrderedDict([('ellim001', 1), ('gyorj001', 1), ('amara001', 1), ('ethia001', 2),
                     ('crawc002', 2), ('gonza003', 2), ('sellj002', 1), ('cabre001', 1),
                     ('maybc001', 1), ('denoc001', 1), ('alony001', 1)])

        >>> g.battersByEvent('single', common.TeamNum.HOME)
        OrderedDict([('gyorj001', 1), ('amara001', 1), ('cabre001', 1),
                     ('maybc001', 1), ('denoc001', 1), ('alony001', 1)])
        '''
        eventDict = OrderedDict()
        for p in self.recordsByType('play'):
            if visitOrHome is not None and p.visitOrHome != visitOrHome:
                continue
            attr = getattr(p.playEvent, eventAttribute)
            if attr is True or (isinstance(attr, int) and attr > 0):
                batter = p.playerId
                if batter not in eventDict:
                    eventDict[batter] = 0
                if attr is True:
                    eventDict[batter] += 1
                else:
                    eventDict[batter] += attr
        return eventDict





class Test(unittest.TestCase):
    pass

    @classmethod
    def setUpClass(cls):
        gc = GameCollection()
        gc.yearStart = 2013
        gc.yearEnd = 2013
        gc.team = 'SDN'
        cls.games = gc.parse()

    def xtestLeadoffBatterLedInning(self):
        pass
#         for hi in g.halfInnings:
#             for p in hi:
#                 if p.record != 'play':
#                     continue
#                 # finish when we can get player by id.

    def xtestInningIteration(self):
        g1 = self.games[0]
        h1 = g1.halfInnings[0]

        pp(h1.following)
        pp(g1.halfInnings[1])
        while h1 is not None:
            print(h1.inningNumber, h1.visitOrHome, '-------------------')
            for x in h1:
                print(x)
            h1 = h1.following

    def testWrongOutsPadres(self):
        unused_totalWrong = 0
        for i, g in enumerate(self.games):
            unused_totalWrong += self.checkSaneOuts(g)
        self.assertEqual(unused_totalWrong, 0)

    def checkSaneOuts(self, g):
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
                pp(half)
                wrong += 1
                for p in half:
                    if p.record == 'play':
                        # noinspection SpellCheckingInspection
                        omop = p.outsMadeOnPlay
                        if omop > 0:
                            pp((p.outsMadeOnPlay, repr(p)))
            self.assertEqual(outs, 3,
                             'Wrong number of outs in game {0}, halfInning {1}: {2} outs'.format(
                                                    g.id, i, outs))

        return wrong


class TestSlow(unittest.TestCase):
    def testAllYears(self):
        import multiprocessing
        import concurrent.futures

        def runOne(y):
            gc = GameCollection()
            gc.yearStart = y
            gc.yearEnd = y
            gc.seasonType = 'regular'
            print(f'Parsing {y}')
            gc.parse()

        max_workers = multiprocessing.cpu_count() - 1
        if max_workers == 0:
            max_workers = 1

        # pylint: disable=broad-except
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            yy = [y for y in range(common.maxRetrosheetYear, 1870, -1)]
            runPath = {executor.submit(runOne, y): y for y in yy}
            for future in concurrent.futures.as_completed(runPath):
                f = runPath[future]
                try:
                    _unused_data = future.result()
                except Exception as exc:
                    print('%r generated an exception: %s' % (f, exc))
                else:
                    print('%r succeeded' % (f))


if __name__ == '__main__':
    from daseki import mainTest
    mainTest(Test)  # Test and/or TestSlow

