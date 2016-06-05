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
DEBUG = False

import os

from daseki import common
from daseki.exceptionsDS import RetrosheetException
from daseki.retro.eventFile import EventFile

class ParserException(RetrosheetException):
    pass

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
        self.eventFileNames = []
        self.rosterFileNames = []
        self.teamFileName = None
        self._eventFiles = []

        self.dirName = None
        self.overrideDirectory = None
        self._files = []

    @property
    def files(self):
        if self._files:
            return self._files

        if self.overrideDirectory:
            dirName = self.overrideDirectory
        else:
            dirName = common.dataRetrosheetByType(self.seasonType)

        self.dirName = dirName
        allFiles = os.listdir(dirName)
        
        files = []
        for f in allFiles:
            if str(self.year) not in f:
                continue
            files.append(f)
            if (f.endswith('.EVA') 
                    or f.endswith('.EVN') 
                    or f.endswith('.EVE') # all-star-game
                ):
                self.eventFileNames.append(f)
            elif f.endswith('.ROS'):
                self.rosterFileNames.append(f)
            elif f.startswith('TEAM'):
                self.teamFileName = f
    
        self._files = files
        return files

    def _parseOneEventFile(self, efn):
        return EventFile(os.path.join(self.dirName, efn))
    
    def parseEventFiles(self):
        '''
        Parses all the event files and returns them as a list.
        '''
        if self._eventFiles:
            return self._eventFiles
        unused_files = self.files
        errors = []
        # 5x slower!
#         for ef in common.multicore(self._parseOneEventFile)(self.eventFileNames):
#             self._eventFiles.append(ef)
        for efn in self.eventFileNames: 
            #try:
                self._eventFiles.append(self._parseOneEventFile(efn))
            #except Exception:
            #    errors.append(efn)
        if errors:
            print("These files had errors: ", errors)
        return self._eventFiles
                
    @property
    def eventFiles(self):
        '''
        returns all EventFiles in the directory.
        '''
        if self._eventFiles:
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
            ret += ev.protoGamesByTeam(teamCode)
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
    

if __name__ == '__main__':
    import daseki
    daseki.mainTest()
