# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         team.py
# Purpose:      information about teams.
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015-16 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
#------------------------------------------------------------------------------
from daseki import common
from collections import namedtuple
import csv
import codecs
import datetime
import os

_teamList = []
TeamInfo = namedtuple('TeamInfo', 'authCode code league division ' + 
                                    'location nickname altnickname startDate endDate city state')

def teamList():
    '''
    >>> tl = team.teamList()
    >>> tl[0]
    TeamInfo(authCode='ANA', code='LAA', 
             league='AL', division='', 
             location='Los Angeles', nickname='Angels', altnickname='', 
             startDate='4/11/1961', endDate='9/1/1965', 
             city='Los Angeles', state='CA')

    :rtype: TeamInfo
    '''
    if any(_teamList):
        return _teamList
    filePath = os.path.join(common.dataFilePath(), 'currentNames.csv')
    with codecs.open(filePath, 'r', 'latin-1') as f:
        for t in csv.reader(f):
            _teamList.append(TeamInfo(*t))
    return _teamList

def teamInfoForCodeAndDate(code, dateStr, searchAuth=False):
    '''
    >>> bees = team.teamInfoForCodeAndDate('BSN', '6/20/1938')
    >>> bees
    TeamInfo(authCode='ATL', code='BSN', 
             league='NL', division='', 
             location='Boston', nickname='Bees', altnickname='', 
             startDate='4/14/1936', endDate='9/29/1940', 
             city='Boston', state='MA')

    Search authoritative codes is off by default:
 
    >>> atlantaIn38 = team.teamInfoForCodeAndDate('ATL', '6/20/1938')
    >>> print(atlantaIn38)
    None
    >>> oldAtlanta = team.teamInfoForCodeAndDate('ATL', '6/20/1938', searchAuth=True)
    >>> oldAtlanta is bees
    True

    :rtype: TeamInfo
    '''
    tl = teamList()
    if hasattr(dateStr, 'month'):
        date = dateStr
    else:
        try:
            date = datetime.datetime.strptime(dateStr, "%m/%d/%Y")
        except ValueError:
            date = datetime.datetime.strptime(dateStr, "%Y/%m/%d")        
    
    for t in tl:
        if searchAuth is False:
            searchCode = t.code
        else:
            searchCode = t.authCode
            
        if code.upper() != searchCode:
            continue
        sdate = datetime.datetime.strptime(t.startDate, '%m/%d/%Y')
        if date < sdate:
            continue
        if t.endDate == "":
            return t
        edate = datetime.datetime.strptime(t.endDate, '%m/%d/%Y')
        if date <= edate:
            return t
    return None
    

def teamInfoForCode(code):
    '''
    Returns a list of information for the code, with the most recent incarnation of
    the team preferred

    :rtype: TeamInfo
    '''
    tl = teamList()
    for t in reversed(tl):
        if code.upper() == t.code:
            return t
    return None

class Team(common.ParentType):
    '''
    Represents a single team, possibly at a single time.
    
    >>> expos = team.Team('MON')
    >>> expos.city
    'Montreal'
    >>> expos.country
    'Canada'
    >>> expos.state # new abbreviation, not 'PQ'
    'QC'
    '''
    regionreps = ('allegheny club', 'tampa bay')
    statereps = ('california', 'colorado', 'florida', 'minnesota', 'texas')
    
    def __init__(self, code=None, date=None, *, parent=None):
        super().__init__(parent=parent)
        self.date = date
        self.authCode = None
        self.organiztion = 'MLB'
        self.level = 'Majors'
        self.league = None
        self.division = None
        self.location = None
        self.city = None
        self.state = None # Province, etc.
        self.country = 'US' # 'Canada' for Toronto, Montreal.  Team may later include Japan, etc.

        self.nickname = None
        self.alternativeNicknames = []
        
        self._currentCode = None
        self.code = code

    def _getCode(self):
        return self._currentCode

    def _setCode(self, code):
        self._currentCode = code
        if code is None:
            return
        t1 = None
        if self.date is not None:
            t1 = teamInfoForCodeAndDate(code, self.date)
        else:
            t1 = teamInfoForCode(code)
        if t1 is None:
            return
        self.league = t1.league
        if t1.division == "":
            self.division = None
        else:
            self.division = t1.division
        
        self.location = t1.location
        if self.location in ('Toronto', 'Montreal'):
            self.country = 'Canada'
        self.city = t1.city
        self.state = t1.state
        if t1.nickname == '(none)':
            self.nickname = None
        else:
            self.nickname = t1.nickname
        if t1.altnickname != "":
            self.alternativeNicknames = t1.altnickname.split(';')
        
    
    code = property(_getCode, _setCode, doc='''
        Gets or sets the code for the team, at the same time changing information if
        possible:
        
        >>> t = team.Team()
        >>> t.code = 'SDN'
        >>> t.city
        'San Diego'
        ''')
    
    @property
    def representsWholeState(self):
        '''
        True if the location is California, Colorado, etc. else False
        
        Of course the Angels never actually represented all of California. Who are we kidding?
        
        >>> t = team.Team('CAL', '1/1/1980')
        >>> t.nickname
        'Angels'
        >>> t.representsWholeState
        True        
        '''
        if self.location is None:
            return False
        return self.location.lower() in self.statereps

    @property
    def representsRegion(self):
        '''
        True if the location is Tampa Bay, Allegheny Club; otherwise False
        
        >>> t = team.Team('TBA')
        >>> t.nickname  # newest name first
        'Rays'
        >>> t.representsRegion
        True
        '''
        if self.location is None:
            return False
        return self.location.lower() in self.regionreps
        


if __name__ == '__main__':
    import daseki
    daseki.mainTest()
    #teamList()

