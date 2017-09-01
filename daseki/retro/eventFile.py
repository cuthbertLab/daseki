# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:       retro/eventFile.py
# Purpose:    loader for eventfile (.EVN, .EVA) files
#
# Authors:    Michael Scott Cuthbert
#
# Copyright:  Copyright © 2015-16 Michael Scott Cuthbert / cuthbertLab
# License:    BSD, see license.txt
#------------------------------------------------------------------------------
import codecs
import csv
import os

from daseki import common
from daseki.retro import protoGame
from daseki.exceptionsDS import RetrosheetException


class EventFile(object):
    '''
    represents and parses one .EVN or .EVA file, 
    which usually represents all games played by a team at home.
    
    Parses them in ProtoGames, stored in the `.protoGames` list.
    
    The other attribute is the "startComments" list which is a list of Comment objects that
    describe the .EVN or .EVA file but not any particular game (such as the encoder's name).

    >>> cards2010 = '2010SLN.EVN'
    
    >>> evf = retro.eventFile.EventFile(cards2010)
    >>> evf
    <daseki.retro.eventFile.EventFile 2010SLN.EVN>
    
    Most files have no comments at the start:
    
    >>> evf.startComments
    []
    
    They all will have a lot of data.  Unstripped lines of code:
    
    >>> len(evf.data)
    12772
    >>> for d in evf.data[0:3]:
    ...     print(d, end='')
    id,SLN201004120
    version,2
    info,visteam,HOU    
    
    And these files have a bunch of :class:`daseki.retro.protoGame.ProtoGame` objects, one
    for every home game, usually 81.
    
    >>> len(evf.protoGames)
    81
    >>> evf.protoGames[0:4]
    [<daseki.retro.protoGame.ProtoGame SLN201004120: HOU at SLN>, 
     <daseki.retro.protoGame.ProtoGame SLN201004140: HOU at SLN>, 
     <daseki.retro.protoGame.ProtoGame SLN201004150: HOU at SLN>,
     <daseki.retro.protoGame.ProtoGame SLN201004160: NYN at SLN>]
          
    '''
    def __init__(self, filename, data=None):
        if os.sep not in filename:
            filename = common.dataRetrosheetByType('regular') + os.sep + filename
        self.filename = filename        
        self.startComments = []
        self.protoGames = []
        if data is None:
            self.readData()
        else:
            self.data = data
        self.protoGames = self.protoGamesFromData(self.data)

    def __repr__(self):
        stripName = self.filename.split(os.sep)[-1]
        return "<%s.%s %s>" % (self.__module__, self.__class__.__name__, 
                                  stripName)
    
    def protoGamesByTeam(self, teamCode):
        '''
        Returns a list of all ProtoGames representing a game played by a single team
        (home or away).
        
        Teams are represented by a three-letter code.
        
        >>> evf = retro.eventFile.EventFile('2010SLN.EVN')
        >>> evf
        <daseki.retro.eventFile.EventFile 2010SLN.EVN>
        >>> evf.protoGamesByTeam('SDN')
        [<daseki.retro.protoGame.ProtoGame SLN201009160: SDN at SLN>, 
         <daseki.retro.protoGame.ProtoGame SLN201009170: SDN at SLN>, 
         <daseki.retro.protoGame.ProtoGame SLN201009180: SDN at SLN>, 
         <daseki.retro.protoGame.ProtoGame SLN201009190: SDN at SLN>]
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

    
    def readData(self, filename=None):
        '''
        Read in the file set in filename or self.filename.
        
        Assumes that the file is encoded as latin-1.
        '''
        if filename is None:
            filename = self.filename
        with codecs.open(self.filename, 'r', 'latin-1') as f:
            data = f.readlines()
        self.data = data

    @staticmethod
    def _lightCSV(line):
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

    def protoGamesFromData(self, data=None):
        '''
        Populates returns a list of ProtoGames by reading in the CSV data in self.data.
        '''
        if data is None:
            data = self.data
        currentProtoGame = None
        protoGames = []
        for dataline in data:
            eventLine = self._lightCSV(dataline)
            
            #common.warn(d)
            eventType = eventLine[0]
            eventData = eventLine[1:]
            if eventType == 'id':
                if currentProtoGame is not None:
                    protoGames.append(currentProtoGame)
                currentProtoGame = protoGame.ProtoGame(eventData[0])
            
            if currentProtoGame is None:
                if eventType != 'com':
                    raise RetrosheetException("Found a non-comment before id: %r" % eventLine)
                self.startComments.append(eventLine)
            else:
                currentProtoGame.append(eventLine)

        if currentProtoGame is not None:
            protoGames.append(currentProtoGame)
    
        return protoGames

def eventFileById(gameId):
    '''
    finds the event file that matches the gameId
    
    >>> efn = retro.eventFile.eventFileById('SDN201304090')
    >>> efn.endswith('daseki/dataFiles/retrosheet/event/regular/2013SDN.EVN')
    True
    
    Last number is optional except for double headers 
    
    >>> efn = retro.eventFile.eventFileById('SDN20130409')
    >>> efn.endswith('daseki/dataFiles/retrosheet/event/regular/2013SDN.EVN')
    True
    
    Returns None if no file be found:
    
    >>> retro.eventFile.eventFileById('CAM18870101') is None
    True
    '''
    gid = common.GameId(gameId)
    eventRegularDir = common.dataRetrosheetByType('regular')
    for ef in os.listdir(eventRegularDir):
        if ef.startswith(str(gid.year) + gid.homeTeam + '.EV'):
            return eventRegularDir + os.sep + ef
    else:
        return None
    
if __name__ == '__main__':
    import daseki
    daseki.mainTest()
    