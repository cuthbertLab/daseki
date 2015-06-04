HOME = 1
VISITOR = 0

DEBUG = False

import os
import codecs
import csv

from bbbalk import common
from bbbalk.exceptionsBB import RetrosheetException

class YearDirectory(object):
    '''
    parses a directory of all the files for a year.
    '''
    def __init__(self, year):
        self.year = year
        dirName = common.dataDirByYear(year)
        self.dirName = dirName
        files = os.listdir(dirName)
        self.files = files
        self.eventFileNames = []
        self.rosterFileNames = []
        self._eventFiles = []
        
        self.teamFileName = None
        for f in files:
            if f.endswith('.EVA') or f.endswith('.EVN'):
                self.eventFileNames.append(f)
            elif f.endswith('.ROS'):
                self.rosterFileNames.append(f)
            elif f.startswith('TEAM'):
                self.teamFileName = f
    
    def parseEventFiles(self):
        if len(self._eventFiles) > 0:
            return self._eventFiles
        errors = []
        for efn in self.eventFileNames: 
            #try:
                self._eventFiles.append(EventFile(os.path.join(self.dirName, efn)))
            #except Exception:
            #    errors.append(efn)
        if len(errors) > 0:
            print("These files had errors: ", errors)
                
    @property
    def eventFiles(self):
        if len(self._eventFiles) > 0:
            return self._eventFiles
        self.parseEventFiles()
        return self._eventFiles
                
    def byTeam(self, teamCode):
        ret = []
        for ev in self.eventFiles:
            ret += ev.byTeam(teamCode)
        return ret

    def byPark(self, teamCode):
        ret = []
        for ev in self.eventFiles:
            ret += ev.byPark(teamCode)
        return ret

    def byUsesDH(self, usedh):
        ret = []
        for ev in self.eventFiles:
            ret += ev.byUsesDH(usedh)
        return ret

    def byDate(self, dateField):
        ret = []
        for ev in self.eventFiles:
            ret += ev.byDate(dateField)
        return ret


class EventFile(object):
    '''
    parses one .EVN or .EVA file
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
        ret = []
        for pg in self.protoGames:
            if pg.hometeam == teamCode or pg.visteam == teamCode:
                ret.append(pg)
        return ret

    def byPark(self, teamCode):
        ret = []
        for pg in self.protoGames:
            if pg.hometeam == teamCode:
                ret.append(pg)
        return ret

    def byUsesDH(self, usedh):
        ret = []
        for pg in self.protoGames:
            if pg.usedh == usedh:
                ret.append(pg)
        return ret

    def byDate(self, dateField):
        ret = []
        for pg in self.protoGames:
            if pg.date == dateField:
                ret.append(pg)
        return ret

    
    def readParse(self):
        with codecs.open(self.filename, 'r', 'latin-1') as f:
            data = f.readlines()
        self.data = data
        self.parseData()

    def parseData(self):
        protoGame = None
        for d in csv.reader(self.data):
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
    '''
    def __init__(self, gameId=None):
        self.id = gameId
        self.hometeam = None  # just enough information to not need
        self.visteam = None   # to parse games unnecessarily
        self.usedh = False
        self.date = None
        self.records = []
    
    def append(self, rec):
        if rec[0] == 'info':
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
    pass
