HOME = 1
VISITOR = 0

DEBUG = False

import os
import codecs
import csv

from collections import namedtuple
Runs = namedtuple('Runs', 'visitor home')

from bbbalk.retro import basic, play, player
from bbbalk.exceptionsBB import RetrosheetException

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

class YearDirectory(object):
    '''
    parses a directory of all the files for a year.
    '''
    def __init__(self, dirName):
        self.dirName = dirName
        files = os.listdir(dirName)
        self.files = files
        self.eventFileNames = []
        self.rosterFileNames = []
        self.eventFiles = []
        
        self.teamFileName = None
        for f in files:
            if f.endswith('.EVA') or f.endswith('.EVN'):
                self.eventFileNames.append(f)
            elif f.endswith('.ROS'):
                self.rosterFileNames.append(f)
            elif f.startswith('TEAM'):
                self.teamFileName = f
    
    def parseEventFiles(self):
        errors = []
        for efn in self.eventFileNames: 
            try:
                self.eventFiles.append(EventFile(os.path.join(self.dirName, efn)))
            except Exception:
                errors.append(efn)
        if len(errors) > 0:
            print("These files had errors: ", errors)
                

class EventFile(object):
    '''
    parses one .EVN or .EVA file
    '''
    def __init__(self, filename, data=None):
        self.filename = filename
        self.records = []
        self.games = []
        self.data = data
        if self.data is None:
            self.readParse()
        else:
            self.parseData()
        
    def readParse(self):
        with codecs.open(self.filename, 'r', 'latin-1') as f:
            data = f.readlines()
        self.data = data
        self.parseData()
        
    def parseData(self):
        game = None
        try:
            for d in csv.reader(self.data):
                eventType = d[0]
                eventData = d[1:]
                eventClass = eventsToClasses[eventType]
                try:
                    if game is not None:
                        parent = game
                    else:
                        parent = self
                    rec = eventClass(parent, *eventData)
                except TypeError:
                    print("Could not parse event: %r in file %s" % (d, self.filename))
                except RetrosheetException as e:
                    print("For file %s got an error: %r " % (self.filename, e))
                    
                self.records.append(rec)
                if rec.record == 'id':
                    if game is not None:
                        if DEBUG:
                            print("\n\n\nParsing Game %s" % game.id)
                        game.finalizeParsing()
                        self.games.append(game)
                    game = Game(rec.id)
                if game is not None:
                    game.records.append(rec)
                elif rec.record != 'com':
                    raise("Found a non-comment before id: %r" % d)
            if game is not None:
                game.finalizeParsing()
                self.games.append(game)
        except AttributeError as e:
            raise RetrosheetException("Error in file: %s: %r " % (self.filename, e))

class Game(object):
    '''
    records information about a game.
    '''
    def __init__(self, gameId):
        self.id = gameId
        self.records = []
        self._hasDH = None
        self._startersHome = []
        self._startersVisitor = []
        self.halfInnings = []

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
