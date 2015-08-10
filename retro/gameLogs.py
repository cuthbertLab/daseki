# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:        gameLogs.py
# Purpose:     retrosheet game log file parsing
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
#------------------------------------------------------------------------------
import codecs
import csv
import os
import unittest

from bbbalk.exceptionsBB import BBBalkException
from bbbalk import common

GameLogCache = {}

def gameLogFilePathForYear(year=2014):
    '''
    Find the path to the game log file for a given year.
    
    >>> glp = retro.gameLogs.gameLogFilePathForYear(2005)
    >>> glp.endswith('bbbalk/dataFiles/gameLogs/GL2005.TXT')
    True
    '''
    yearStr = str(year)
    path = common.gameLogFilePath()
    return os.path.join(path, "GL" + yearStr + ".TXT")

def gameLogsForYear(year=2014):
    '''
    Get all the game logs for a given year as a list of lists.
    
    >>> gls = retro.gameLogs.gameLogsForYear(2014)
    >>> len(gls)
    2430
    >>> int(162 * 30 / 2)
    2430
    >>> gls[0][0:7]
    ['20140322', '0', 'Sat', 'LAN', 'NL', '1', 'ARI']

    Second parse of the same logs will return from cache, so there's no
    penalty for reparsing multiple times.
    
    >>> gls2 = retro.gameLogs.gameLogsForYear(2014)
    >>> gls2 is gls
    True
    '''
    if year in GameLogCache:
        return GameLogCache[year]
    fp = gameLogFilePathForYear(year)
    with codecs.open(fp, 'r', 'latin-1') as f:
        csvR = csv.reader(f)
        data = list(csvR)
    GameLogCache[year] = data
    return data

def gameLogRawById(gameId):
    '''
    Find the game log that matches a given retrosheet ID as a 
    raw data list (use the GameLog object normally)
    
    >>> glRaw = retro.gameLogs.gameLogRawById('ARI201403220')
    >>> glRaw
    ['20140322', '0', 'Sat', 'LAN', 'NL', '1', 'ARI', 'NL', ...]
    '''
    gid = common.GameId(gameId)
    logs = gameLogsForYear(gid.year)
    gameLogId = "{g.year:4d}{g.month:02d}{g.day:02d}".format(g=gid)
    foundCorrectLogId = False
    potentialGames = [] # for doubleHeaders
    for l in logs:
        if l[0] == gameLogId and l[6] == gid.homeTeam:
            potentialGames.append(l)
            foundCorrectLogId = True
        elif l[0] != gameLogId and foundCorrectLogId is True:
            break
    if len(potentialGames) == 1:
        return potentialGames[0]
    elif len(potentialGames) > 1:
        for pg in potentialGames:
            gameNumber = pg[1]
            if gid.gameNum == "1" and gameNumber in ('1', 'A'):
                return pg
            elif gid.gameNum == "2" and gameNumber in ('2', 'B'):
                return pg
            elif gid.gameNum == "3" and gameNumber == "3": # triple header!
                return pg
        raise BBBalkException("Could not find the right game for a double/triple header!")
    return None
        
class GameLog(object):
    '''
    Get a nicer object that allows for accessing gameLog information
    by name. Also knows what information should be returned as an int
    and converts the data accordingly.
    
    >>> gl = retro.gameLogs.GameLog('ARI201403220')
    >>> gl.date
    '20140322'
    >>> gl.data[0] is gl.date
    True
    
    >>> gl.gameNumber
    '0'
    >>> gl.dayOfWeek
    'Sat'
    >>> gl.visitTeam
    'LAN'
    >>> gl.homeTeam
    'ARI'
    
    >>> gl.visitRuns
    3
    >>> gl.homeRuns
    1
    >>> for i in gl.labels:
    ...    print(i, repr(getattr(gl, i)))
    date '20140322'
    gameNumber '0'
    dayOfWeek 'Sat'
    visitTeam 'LAN'
    visitLeague 'NL'
    visitTeamGameNumber 1
    homeTeam 'ARI'
    homeLeague 'NL'
    homeTeamGameNumber 1
    visitRuns 3
    homeRuns 1
    numberOfOuts 54
    dayNightIndicator 'N'
    completionInformation ''
    forfeitInformation ''
    protestInformation ''
    parkId 'SYD01'
    attendance 38266
    lengthOfGame 169
    visitLineScore '010200000'
    homeLineScore '000001000'
    visitAtBats 33
    visitHits 5
    visitDoubles 2
    visitTriples 0
    visitHomeRuns 1
    visitRunsBattedIn 3
    visitSacrificeHits 0
    visitSacrificeFlies 0
    visitHitByPitch 1
    visitBaseOnBalls 3
    visitBaseOnBallsIntentional 0
    visitStrikeouts 11
    visitStolenBases 0
    visitCaughtStealing 0
    visitGroundedIntoDblPlay 0
    visitCatcherInterference 0
    visitLeftOnBase 7
    visitPitchersUsed 4
    visitIndividualEarnedRuns 1
    visitTeamEarnedRuns 1
    visitWildPitches 1
    visitBalks 0
    visitPutOuts 27
    visitAssists 13
    visitErrors 1
    visitPassedBalls 0
    visitDblPlays 0
    visitTplPlays 0
    homeAtBats 33
    homeHits 5
    homeDoubles 1
    homeTriples 0
    homeHomeRuns 0
    homeRunsBattedIn 1
    homeSacrificeHits 0
    homeSacrificeFlies 0
    homeHitByPitch 0
    homeBaseOnBalls 2
    homeBaseOnBallsIntentional 0
    homeStrikeouts 10
    homeStolenBases 0
    homeCaughtStealing 0
    homeGroundedIntoDblPlay 0
    homeCatcherInterference 0
    homeLeftOnBase 7
    homePitchersUsed 5
    homeIndividualEarnedRuns 3
    homeTeamEarnedRuns 3
    homeWildPitches 1
    homeBalks 0
    homePutOuts 27
    homeAssists 10
    homeErrors 1
    homePassedBalls 0
    homeDblPlays 0
    homeTplPlays 0
    plateUmpireId 'welkt901'
    plateUmpireName 'Tim Welke'
    firstBaseUmpireId 'scotd901'
    firstBaseUmpireName 'Dale Scott'
    secondBaseUmpireId 'diazl901'
    secondBaseUmpireName 'Laz Diaz'
    thirdBaseUmpireId 'carlm901'
    thirdBaseUmpireName 'Mark Carlson'
    leftFieldUmpireId ''
    leftFieldUmpireName '(none)'
    rightFieldUmpireId ''
    rightFieldUmpireName '(none)'
    visitManagerId 'mattd001'
    visitManagerName 'Don Mattingly'
    homeManagerId 'gibsk001'
    homeManagerName 'Kirk Gibson'
    winningPitcherId 'kersc001'
    winningPitcherName 'Clayton Kershaw'
    losingPitcherId 'milew001'
    losingPitcherName 'Wade Miley'
    savingPitcherId 'jansk001'
    savingPitcherName 'Kenley Jansen'
    gameWinningRBIId 'ethia001'
    gameWinningRBIName 'Andre Ethier'
    visitStartingPitcherId 'kersc001'
    visitStartingPitcherName 'Clayton Kershaw'
    homeStartingPitcherId 'milew001'
    homeStartingPitcherName 'Wade Miley'
    visitStartingBat1Id 'puigy001'
    visitStartingBat1Name 'Yasiel Puig'
    visitStartingBat1Position 9
    visitStartingBat2Id 'turnj001'
    visitStartingBat2Name 'Justin Turner'
    visitStartingBat2Position 4
    visitStartingBat3Id 'ramih003'
    visitStartingBat3Name 'Hanley Ramirez'
    visitStartingBat3Position 6
    visitStartingBat4Id 'gonza003'
    visitStartingBat4Name 'Adrian Gonzalez'
    visitStartingBat4Position 3
    visitStartingBat5Id 'vanss001'
    visitStartingBat5Name 'Scott Van Slyke'
    visitStartingBat5Position 7
    visitStartingBat6Id 'uribj002'
    visitStartingBat6Name 'Juan Uribe'
    visitStartingBat6Position 5
    visitStartingBat7Id 'ethia001'
    visitStartingBat7Name 'Andre Ethier'
    visitStartingBat7Position 8
    visitStartingBat8Id 'ellia001'
    visitStartingBat8Name 'A.J. Ellis'
    visitStartingBat8Position 2
    visitStartingBat9Id 'kersc001'
    visitStartingBat9Name 'Clayton Kershaw'
    visitStartingBat9Position 1
    homeStartingBat1Id 'polla001'
    homeStartingBat1Name 'A.J. Pollock'
    homeStartingBat1Position 8
    homeStartingBat2Id 'hilla001'
    homeStartingBat2Name 'Aaron Hill'
    homeStartingBat2Position 4
    homeStartingBat3Id 'goldp001'
    homeStartingBat3Name 'Paul Goldschmidt'
    homeStartingBat3Position 3
    homeStartingBat4Id 'pradm001'
    homeStartingBat4Name 'Martin Prado'
    homeStartingBat4Position 5
    homeStartingBat5Id 'trumm001'
    homeStartingBat5Name 'Mark Trumbo'
    homeStartingBat5Position 7
    homeStartingBat6Id 'montm001'
    homeStartingBat6Name 'Miguel Montero'
    homeStartingBat6Position 2
    homeStartingBat7Id 'owinc001'
    homeStartingBat7Name 'Chris Owings'
    homeStartingBat7Position 6
    homeStartingBat8Id 'parrg001'
    homeStartingBat8Name 'Gerardo Parra'
    homeStartingBat8Position 9
    homeStartingBat9Id 'milew001'
    homeStartingBat9Name 'Wade Miley'
    homeStartingBat9Position 1
    additionalInformation ''
    acquisitionInformation 'Y'    
    '''
    labels = '''date gameNumber dayOfWeek visitTeam visitLeague visitTeamGameNumber
    homeTeam homeLeague homeTeamGameNumber visitRuns homeRuns 
    numberOfOuts dayNightIndicator completionInformation 
    forfeitInformation protestInformation parkId attendance 
    lengthOfGame visitLineScore homeLineScore 
    visitAtBats visitHits visitDoubles visitTriples visitHomeRuns visitRunsBattedIn
    visitSacrificeHits visitSacrificeFlies visitHitByPitch visitBaseOnBalls 
    visitBaseOnBallsIntentional visitStrikeouts visitStolenBases 
    visitCaughtStealing visitGroundedIntoDblPlay visitCatcherInterference 
    visitLeftOnBase 
    visitPitchersUsed visitIndividualEarnedRuns visitTeamEarnedRuns visitWildPitches visitBalks 
    visitPutOuts visitAssists visitErrors visitPassedBalls visitDblPlays visitTplPlays 
    homeAtBats homeHits homeDoubles homeTriples homeHomeRuns homeRunsBattedIn
    homeSacrificeHits homeSacrificeFlies homeHitByPitch homeBaseOnBalls 
    homeBaseOnBallsIntentional homeStrikeouts homeStolenBases 
    homeCaughtStealing homeGroundedIntoDblPlay homeCatcherInterference 
    homeLeftOnBase 
    homePitchersUsed homeIndividualEarnedRuns homeTeamEarnedRuns homeWildPitches homeBalks 
    homePutOuts homeAssists homeErrors homePassedBalls homeDblPlays homeTplPlays 
    plateUmpireId plateUmpireName 
    firstBaseUmpireId firstBaseUmpireName 
    secondBaseUmpireId secondBaseUmpireName 
    thirdBaseUmpireId thirdBaseUmpireName 
    leftFieldUmpireId leftFieldUmpireName 
    rightFieldUmpireId rightFieldUmpireName 
    visitManagerId visitManagerName 
    homeManagerId homeManagerName 
    winningPitcherId winningPitcherName 
    losingPitcherId losingPitcherName 
    savingPitcherId savingPitcherName 
    gameWinningRBIId gameWinningRBIName 
    visitStartingPitcherId visitStartingPitcherName 
    homeStartingPitcherId homeStartingPitcherName 
    visitStartingBat1Id visitStartingBat1Name visitStartingBat1Position 
    visitStartingBat2Id visitStartingBat2Name visitStartingBat2Position 
    visitStartingBat3Id visitStartingBat3Name visitStartingBat3Position 
    visitStartingBat4Id visitStartingBat4Name visitStartingBat4Position 
    visitStartingBat5Id visitStartingBat5Name visitStartingBat5Position 
    visitStartingBat6Id visitStartingBat6Name visitStartingBat6Position 
    visitStartingBat7Id visitStartingBat7Name visitStartingBat7Position 
    visitStartingBat8Id visitStartingBat8Name visitStartingBat8Position 
    visitStartingBat9Id visitStartingBat9Name visitStartingBat9Position 
    homeStartingBat1Id homeStartingBat1Name homeStartingBat1Position 
    homeStartingBat2Id homeStartingBat2Name homeStartingBat2Position 
    homeStartingBat3Id homeStartingBat3Name homeStartingBat3Position 
    homeStartingBat4Id homeStartingBat4Name homeStartingBat4Position 
    homeStartingBat5Id homeStartingBat5Name homeStartingBat5Position 
    homeStartingBat6Id homeStartingBat6Name homeStartingBat6Position 
    homeStartingBat7Id homeStartingBat7Name homeStartingBat7Position 
    homeStartingBat8Id homeStartingBat8Name homeStartingBat8Position 
    homeStartingBat9Id homeStartingBat9Name homeStartingBat9Position 
    additionalInformation 
    acquisitionInformation 
    '''.split()
    intLabels = set('''visitTeamGameNumber homeTeamGameNumber visitRuns homeRuns numberOfOuts attendance lengthOfGame
    visitAtBats visitHits visitDoubles visitTriples visitHomeRuns visitRunsBattedIn
    visitSacrificeHits visitSacrificeFlies visitHitByPitch visitBaseOnBalls 
    visitBaseOnBallsIntentional visitStrikeouts visitStolenBases 
    visitCaughtStealing visitGroundedIntoDblPlay visitCatcherInterference 
    visitLeftOnBase 
    visitPitchersUsed visitIndividualEarnedRuns visitTeamEarnedRuns visitWildPitches visitBalks 
    visitPutOuts visitAssists visitErrors visitPassedBalls visitDblPlays visitTplPlays 
    homeAtBats homeHits homeDoubles homeTriples homeHomeRuns homeRunsBattedIn
    homeSacrificeHits homeSacrificeFlies homeHitByPitch homeBaseOnBalls 
    homeBaseOnBallsIntentional homeStrikeouts homeStolenBases 
    homeCaughtStealing homeGroundedIntoDblPlay homeCatcherInterference 
    homeLeftOnBase 
    homePitchersUsed homeIndividualEarnedRuns homeTeamEarnedRuns homeWildPitches homeBalks 
    homePutOuts homeAssists homeErrors homePassedBalls homeDblPlays homeTplPlays 
    visitStartingBat1Position
    visitStartingBat2Position
    visitStartingBat3Position
    visitStartingBat4Position
    visitStartingBat5Position
    visitStartingBat6Position
    visitStartingBat7Position
    visitStartingBat8Position    
    visitStartingBat9Position
    homeStartingBat1Position
    homeStartingBat2Position
    homeStartingBat3Position
    homeStartingBat4Position
    homeStartingBat5Position
    homeStartingBat6Position
    homeStartingBat7Position
    homeStartingBat8Position
    homeStartingBat9Position
    '''.split())
    
    def __init__(self, gameId=None):
        self.data = None
        if gameId is not None:
            self.data = gameLogRawById(gameId)
    
    def __getattr__(self, attr):
        if attr in self.labels:
            v = self.data[self.labels.index(attr)]
            if attr in self.intLabels:
                try:
                    v = int(v)
                except ValueError:
                    e = "{0} {1} {2}".format(attr, self.labels.index(attr) + 1, repr(v))
                    raise ValueError(e)
            return v
        return None

class Test(unittest.TestCase):
    pass

class TestSlow(unittest.TestCase):
    def testRunInformation(self):
        from bbbalk import games
        gc = games.GameCollection()
        #gc.yearStart = 1995
        #gc.yearEnd = 2009
        gc.park = 'BAL' # doubleheader game makes a nice test.
        for g in gc.parse():
            gId = g.id
            visitRuns = g.runs.visitor
            homeRuns = g.runs.home
            gl = GameLog(gId)
            self.assertEqual(visitRuns, gl.visitRuns, "{0}: PlayData {1} GameLog {2}".format(gId, visitRuns, gl.visitRuns))
            self.assertEqual(homeRuns, gl.homeRuns, "{0}: PlayData {1} GameLog {2}".format(gId, homeRuns, gl.homeRuns))

if __name__ == "__main__":
    import bbbalk
    bbbalk.mainTest(Test)