# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:        retro/protoGame.py
# Purpose:     light representation of a game in retrosheet event file format
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015-22 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------

class ProtoGame(object):
    '''
    A collection of barely parsed game data to be turned into a Game file.

    It is distinct from a real Game object because we have only parsed enough
    information to be able to filter out whether this object is worth parsing fuller.

    For instance, if you are only interested in games of a particular team or played
    at a particular park, then there's no need to parse every file in a directory.
    Instead, we just parse all the files quickly into ProtoGames
    and filter out games further.

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
        return (f'<{self.__module__}.{self.__class__.__name__} '
                f'{self.id}: {self.visteam} at {self.hometeam}>')

    def append(self, rec):
        '''
        Append a record into self.records but
        update team information in the process.
        '''
        self.records.append(rec)
        if rec[0] != 'info':
            return

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


def protoGameById(gameId):
    '''
    Given the id set in self.id, find the appropriate file and proto parse it into this
    ProtoGame object.

    Not an efficient way of doing this for many games (because all games in the
    file need to be parsed into protoIds). But useful for looking at one single game
    or for demonstration purposes

    >>> from daseki import retro
    >>> retro.protoGame.protoGameById('SDN201304090')
    <daseki.retro.protoGame.ProtoGame SDN201304090: LAN at SDN>

    Last digit is optional:

    >>> retro.protoGame.protoGameById('SDN20130409')
    <daseki.retro.protoGame.ProtoGame SDN201304090: LAN at SDN>
    '''
    from daseki.retro import eventFile
    ef = eventFile.eventFileById(gameId)
    efo = eventFile.EventFile(ef)
    if len(gameId) == 11:
        gameId += '0'
    for pg in efo.protoGames:
        if pg.id == gameId:
            return pg

if __name__ == '__main__':
    import daseki
    daseki.mainTest()
