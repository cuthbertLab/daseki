# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:        parser.py
# Purpose:     retrosheet file parsing
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
#------------------------------------------------------------------------------

HOME = 1
VISITOR = 0

DEBUG = False

import os
import codecs
import csv

from daseki import common
from daseki.exceptionsDS import RetrosheetException

class ParserException(RetrosheetException):
    pass

def protoGameById(gameId):
    '''
    Given the id set in self.id, find the appropriate file and proto parse it into this
    ProtoGame object.
    
    Not an efficient way of doing this for many games (because all games in the 
    file need to be parsed). But useful for looking at one.
    
    >>> retro.parser.protoGameById('SDN201304090')
    <daseki.retro.parser.ProtoGame SDN201304090: LAN at SDN>    

    Last digit is optional:

    >>> retro.parser.protoGameById('SDN20130409')
    <daseki.retro.parser.ProtoGame SDN201304090: LAN at SDN>    

    '''
    ef = findFileById(gameId)
    efo = EventFile(ef)
    if len(gameId) == 11:
        gameId += "0"
    for pg in efo.protoGames:
        if pg.id == gameId:
            return pg

def findFileById(gameId):
    '''
    finds the event file that matches the gameId
    
    >>> efn = retro.parser.findFileById('SDN201304090')
    >>> efn.endswith('daseki/dataFiles/retrosheet/event/regular/2013SDN.EVN')
    True
    
    Last number is optional except for double headers 
    
    >>> efn = retro.parser.findFileById('SDN20130409')
    >>> efn.endswith('daseki/dataFiles/retrosheet/event/regular/2013SDN.EVN')
    True
    '''
    gid = common.GameId(gameId)
    yd = YearDirectory(gid.year)
    for ef in yd.eventFileNames:
        if ef.startswith(str(gid.year) + gid.homeTeam + '.EV'):
            return yd.dirName + os.sep + ef
    else:
        return None

class YearDirectory(object):
    '''
    A YearDirectory represents and parses a virtual directory of all the files for a year.
    
    You can optionally call `.parseEventFiles()` to load them all into ProtoGames, however calling
    any of the methods below will parse them automatically.
    
    It has these attributes:
    
    year -- four-digit year code
    dirName -- path to the directory containing files for that year
    files -- list of (short) filenames in the directory.
    eventFileNames -- list of (short) filenames in the directory that contain game events
    rosterFileNames -- list of (short) filenames in the directory that contain rosters for teams
    teamFileName -- string of the filename that gives the list of teams playing thatyear.
    '''
    def __init__(self, year, seasonType='regular'):
        self.year = year
        self.seasonType = seasonType
        dirName = common.dataRetrosheetByType(seasonType)
        self.dirName = dirName
        allFiles = os.listdir(dirName)
        self.eventFileNames = []
        self.rosterFileNames = []
        self.teamFileName = None
        self._eventFiles = []
        
        files = []
        for f in allFiles:
            if str(year) not in f:
                continue
            files.append(f)
            if f.endswith('.EVA') or f.endswith('.EVN'):
                self.eventFileNames.append(f)
            elif f.endswith('.ROS'):
                self.rosterFileNames.append(f)
            elif f.startswith('TEAM'):
                self.teamFileName = f
    
        self.files = files
        
    def _parseOneEventFile(self, efn):
        return EventFile(os.path.join(self.dirName, efn))
    
    def parseEventFiles(self):
        '''
        Parses all the event files and returns them as a list.
        '''
        if any(self._eventFiles):
            return self._eventFiles
        errors = []
        # 5x slower!
#         for ef in common.multicore(self._parseOneEventFile)(self.eventFileNames):
#             self._eventFiles.append(ef)
        for efn in self.eventFileNames: 
            #try:
                self._eventFiles.append(self._parseOneEventFile(efn))
            #except Exception:
            #    errors.append(efn)
        if any(errors):
            print("These files had errors: ", errors)
        return self._eventFiles
                
    @property
    def eventFiles(self):
        '''
        returns all EventFiles in the directory.
        '''
        if any(self._eventFiles):
            return self._eventFiles
        self.parseEventFiles()
        return self._eventFiles
                
                
    def all(self):
        ret = []
        for ev in self.eventFiles:
            ret += ev.protoGames
        return ret
        
    def byTeam(self, teamCode):
        '''
        Returns a list of all ProtoGames (in any event file) representing a 
        game played by a single team (home or away).
        
        The teamCode is a three-letter abbreviation such as "ANA", "HOU" etc.
        
        TODO: allow for other team names.
        '''
        ret = []
        for ev in self.eventFiles:
            ret += ev.byTeam(teamCode)
        return ret

    def byPark(self, teamCode):
        '''
        Returns a list of all ProtoGames (in any event file) representing a game played by 
        a single team at home -- does not actually distinguish between the few cases where a 
        team might play a "home" game at a different ballpark, such as the Montreal
        Expos in San Juan.
        '''
        ret = []
        for ev in self.eventFiles:
            ret += ev.byPark(teamCode)
        return ret

    def byUsesDH(self, usedh):
        '''
        Returns a list of all ProtoGames representing a game played with a designated hitter
        (if usedh is True) or without a designated hitter (if usedh is False).
        '''
        ret = []
        for ev in self.eventFiles:
            ret += ev.byUsesDH(usedh)
        return ret

    def byDate(self, dateField):
        '''
        Returns a list of all ProtoGames representing games played on a given date.
        
        See the EventFile.byDate method for explanation of dateField object
        '''
        ret = []
        for ev in self.eventFiles:
            ret += ev.byDate(dateField)
        return ret


class EventFile(object):
    '''
    parses one .EVN or .EVA file, which usually represents all games played by a team at home.
    
    Parses them in ProtoGames, stored in the `.protoGames` list.
    
    The other attribute is the "startComments" list which is a list of Comment objects that
    describe the .EVN or .EVA file but not any particular game (such as the encoder's name).
    '''
    def __init__(self, filename, data=None):
        self.filename = filename
        self.startComments = []
        self.protoGames = []
        self.data = data
        if self.data is None:
            self.readParse()
        else:
            self.parseData()
    
    def byTeam(self, teamCode):
        '''
        Returns a list of all ProtoGames representing a game played by a single team
        (home or away).
        
        Teams are represented by a three-letter code.
        '''
        ret = []
        for pg in self.protoGames:
            if pg.hometeam == teamCode or pg.visteam == teamCode:
                ret.append(pg)
        return ret

    def byPark(self, teamCode):
        '''
        Returns a list of all ProtoGames representing a game played by a single team
        at home -- does not actually distinguish between the few cases where a 
        team might play a "home" game at a different ballpark, such as the Montreal
        Expos in San Juan.
        '''
        ret = []
        for pg in self.protoGames:
            if pg.hometeam == teamCode:
                ret.append(pg)
        return ret

    def byUsesDH(self, usedh):
        '''
        Returns a list of all ProtoGames representing a game played with a designated hitter
        (if usedh is True) or without a designated hitter (if usedh is False).
        '''
        ret = []
        for pg in self.protoGames:
            if pg.usedh == usedh:
                ret.append(pg)
        return ret

    def byDate(self, dateField):
        '''
        Returns a list of all ProtoGames representing games played on a given date.
        
        The date filed should be something like: 1999/04/12
        '''
        ret = []
        for pg in self.protoGames:
            if pg.date == dateField:
                ret.append(pg)
        return ret

    
    def readParse(self, filename=None):
        '''
        Read in the file set in filename or self.filename.
        
        Assumes that the file is encoded as latin-1.
        '''
        if filename is None:
            filename = self.filename
        with codecs.open(self.filename, 'r', 'latin-1') as f:
            data = f.readlines()
        self.data = data
        self.parseData()

    def lightCSV(self, line):
        '''
        The python csv.reader is very powerful, but also very slow.  So, what we
        do is a normal parse most of the time, but use csv reader if there is a quotation
        mark...
        '''
        if '"' not in line:
            return line.rstrip().split(',')
        else:
            for d in csv.reader([line]):
                return d

    def parseData(self):
        '''
        Populates self.protoGames by reading in the CSV data in self.data.
        '''
        protoGame = None
        for l in self.data:
            d = self.lightCSV(l)
            
            #common.warn(d)
            eventType = d[0]
            eventData = d[1:]
            if eventType == 'id':
                if protoGame is not None:
                    self.protoGames.append(protoGame)
                protoGame = ProtoGame(eventData[0])
            if protoGame is None:
                if eventType != 'com':
                    raise RetrosheetException("Found a non-comment before id: %r" % d)
                self.startComments.append(d)
            else:
                protoGame.append(d)
        if protoGame is not None:
            self.protoGames.append(protoGame)
    
class ProtoGame(object):
    '''
    A collection of barely parsed game data to be turned into a Game file.
    
    It is distinct from a real Game object because we have only parsed enough
    information to be able to filter out whether this object is worth parsing fuller.
    
    For instance, if you are only interested in games of a particular team or played
    at a particular park, then there's no need to parse every file in a directory. Instead
    we just parse all the files quickly into ProtoGames and filter out games further.
    
    Attributes are:
    
    id -- gameId
    hometeam -- home team 3-letter code
    visteam -- visiting team 3-letter code
    usedh -- used designated hitter (True or False)
    date -- date of the game in the form 2003/10/01 
    '''
    def __init__(self, gameId=None):
        self.id = gameId
        self.hometeam = None  # just enough information to not need
        self.visteam = None   # to parse games unnecessarily
        self.usedh = False
        self.date = None
        self.records = []     
    
    def __repr__(self):
        return "<%s.%s %s: %s at %s>" % (self.__module__, self.__class__.__name__, 
                                  self.id, self.visteam, self.hometeam)
        
    
    def append(self, rec):
        '''
        Append a record into self.records but update team information in the process.
        '''
        if rec[0] is not 'info':
            if rec[1] == 'visteam':
                self.visteam = rec[2]
            elif rec[1] == 'hometeam':
                self.hometeam = rec[2]
            elif rec[1] == 'usedh':
                if rec[2] == 'true':
                    self.usedh = True
                else:
                    self.usedh = False
            elif rec[1] == 'date':
                self.date = rec[2]
        self.records.append(rec)


if __name__ == '__main__':
    import daseki
    daseki.mainTest()
