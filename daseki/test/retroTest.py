# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         test/retroTest.py
# Purpose:      Tests of Retrosheet information
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015-16 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
#-------------------------------------------------------------------------------
import unittest
import os
from daseki import common
from daseki.retro.parser import EventFile, YearDirectory # @UnresolvedImport
from daseki.game import Game # @UnresolvedImport

class TestExternal(unittest.TestCase):
    def sdAttendance(self):
        yd = YearDirectory(2014)
        attd = 0
        for pg in yd.byTeam('SDN'):
            g = Game()
            g.mergeProto(pg)
            att = g.infoByType('attendance')
            print(g.id, att)
            attd += int(att)
        print("******", attd)

    def yearsList(self, start=1995, end=2014):
        for thisYear in range(start, end+1):
            print("Parsing: ", thisYear)
            yd = YearDirectory(thisYear)
            yd.parseEventFiles()
            
    def testYearList(self, year=2014):
        yd = YearDirectory(year)
        yd.parseEventFiles()
    
    def pitcherBats(self):
        '''
        how often did the pitcher bat in the first inning?
        
        1995-2014:
        games 25140 
        happened 11552 
        420 times in the first inning
        percentage 45% 

        2010-2015
        43% of time.
        '''
        gamesPitched = {}
        
        for thisYear in range(2010, 2015):
            yd = YearDirectory(thisYear)
            yd.parseEventFiles()
            
            for ev in yd.eventFiles:
                for pg in ev.protoGames:
                    g = pg.parse()
                    visitorTeam = g.visitingTeam
                    if visitorTeam not in gamesPitched:
                        gamesPitched[visitorTeam] = [0, 0, 0]
                    if not g.hasDH():
                        gamesPitched[visitorTeam][0] += 1
                        starters = g.starters(common.TeamNum.VISITOR)
                        startingPitcher = starters[-1] # TODO: get by position
                        #print(startingPitcher.name)
                        for r in g.recordsByType('play'):
                            if (r.inning <= 2 and 
                                    r.visitOrHome == common.TeamNum.VISITOR and 
                                    r.playerId == startingPitcher.id):
                                #print("********Yup")
                                gamesPitched[visitorTeam][r.inning] += 1

        totTot = 0
        totTotUsed = 0
        totTot1st = 0
        
        for tn in sorted(gamesPitched):
            totalGames = gamesPitched[tn][0]
            i1 = gamesPitched[tn][1] 
            i2 = gamesPitched[tn][2] 
            totalPitcherUsed = i1 + i2
            percentage = int(100 * totalPitcherUsed/(totalGames+0.00001))
            totTot += totalGames
            totTotUsed += totalPitcherUsed
            totTot1st += i1
            if (totalGames > 10):
                print(tn, totalGames, totalPitcherUsed, percentage, i1, i2)
        
        percentage = int(100 * totTotUsed/totTot)
        print("***", totTot, totTotUsed, percentage, totTot1st)
    
    def events(self):
        ev = EventFile(os.path.join(common.dataRetrosheetEvent(), 'regular', '2014SDN.EVN'))
        g = Game()
        g.mergeProto(ev.protoGames[0])
        for p in g.recordsByType('play'):
            e = p.playEvent
            print(p.inning, p.visitOrHome, p.playerId, e.basicBatter, e.isOut, e.isSafe, e.raw)
            p.runnerEvent

    def xtestScores(self):
        from daseki.retro import gameLogs
        global DEBUG
        DEBUG = True
        ev = EventFile(os.path.join(common.dataRetrosheetEvent(), 'regular', '2014SDN.EVN'))
        for pg in ev.protoGames:
            g = Game()
            g.mergeProto(pg)
            r = g.runs
            gl = gameLogs.GameLog(g.id)
            #print(g.id, g.runs)
            self.assertEqual(gl.homeRuns, r.home)
            self.assertEqual(gl.visitRuns, r.visitor)
    
    
    def leadoffsLeadoff(self):
        from daseki import game  # @UnresolvedImport
        t = common.Timer()
        gc = game.GameCollection()
        gc.yearStart = 2000
        gc.yearEnd = 2014
        gc.usesDH = True
        gs = gc.parse()
        totalPAs = 0
        totalLeadOffs = 0
        for g in gs:
            for hi in g.halfInnings:
                for p in hi.plateAppearances:
                    if p.battingOrder == 1:
                        totalPAs += 1
                        if p.plateAppearanceInInning == 1:
                            totalLeadOffs += 1
        print(totalPAs, totalLeadOffs, totalLeadOffs*100/totalPAs)
        print(t(), 'seconds')
        
    def testRunsAboveAverage(self):
        pId = {}
        expectation = {}
        from daseki import game, core
        #from daseki.common import TeamNum
        gc = game.GameCollection()
        gc.yearStart = 1987
        gc.yearEnd = 1987
        #gc.team = 'SDN'
        gc.parse()
        
        erm = core.ExpectedRunMatrix()
        
        for g in gc.games:
            for hi in g.halfInnings:
                #if hi.visitOrHome != SD:
                #    continue
                for pa in hi.plateAppearances:
                    le = pa.lastEvent
                    bId = le.playerId
                    if bId not in pId:
                        pId[bId] = 0
                        expectation[bId] = 0
                    pId[bId] += 1
                    runsExpectedBefore = erm.runsForSituation(le.runnersBefore, pa.outsBefore)
                    runsExpectedAfter = erm.runsForSituation(le.runnersAfter, pa.outsAfter)
                    runsScored = le.runnerEvent.runs
                    expectation[bId] += runsScored + runsExpectedAfter - runsExpectedBefore

        for b in sorted(pId, key=lambda x: expectation[x]):
            print("{0:10} {1:+0.3f} {2:+4.1f}".format(b, expectation[b]/pId[b], expectation[b]))
        
        
if __name__ == '__main__':
    import daseki
    daseki.mainTest(TestExternal)
