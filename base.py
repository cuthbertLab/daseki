# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         __init__.py
# Purpose:      BBBalk -- A toolkit for computational baseball analysis 
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2014-15 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
#------------------------------------------------------------------------------
from __future__ import print_function
from __future__ import division


import copy

from bbbalk.testRunner import mainTest
from bbbalk import common
#from exceptionsBB import BBBalkException

VISITOR = 0
HOME = 1

# class Inning(object):
#     def __init__(self, inningNumber = 1, visitorHalf = None, homeHalf = None):
#         self.inningNumber = inningNumber
#         self.visitorHalf = visitorHalf
#         self.homeHalf = homeHalf

class HalfInning(common.ParentType):
    @common.keyword_only_args('parent')    
    def __init__(self, inningNumber = 1, visitorHome = VISITOR, parent=None):
        super(HalfInning, self).__init__(parent=parent)
        self.inningNumber = inningNumber
        self.visitorHome = visitorHome
        self.events = []
        self._iterindex = 0
        
    def append(self, other):
        self.events.append(other)

    def __iter__(self):
        self._iterindex = 0
        return self
    
    def __next__(self):
        i = self._iterindex
        if i >= len(self.events):
            raise StopIteration        
        self._iterindex += 1
        return self.events[i]

    def __getitem__(self, k):
        return self.events[k]


class BaseRunners(common.ParentType):
    '''
    A relatively lightweight object for dealing with baserunners.
    
    >>> br = base.BaseRunners(False, 'cuthbert', 'hamilton')
    >>> br
    <bbbalk.base.BaseRunners 1:False 2:cuthbert 3:hamilton>
    >>> str(br)
    '1:False 2:cuthbert 3:hamilton'
    >>> br.first
    False
    >>> br.third
    'hamilton'
    >>> for b in br:
    ...     print(b)
    False
    cuthbert
    hamilton
    
    Can pass in a parent object.
    
    >>> br = base.BaseRunners(False, 'cuthbert', 'hamilton', parent=object)
    >>> br[1]
    'cuthbert'
    >>> br[2] = 'elina'
    >>> br.third
    'elina'
    '''
    __slots__ = ('first', 'second', 'third', '_iterindex') 
    @common.keyword_only_args('parent')
    def __init__(self, first=False, second=False, third=False, parent=None):
        super(BaseRunners, self).__init__(parent=parent)
        self.first = first
        self.second = second
        self.third = third
        self._iterindex = 0
        if type(first) in (list, tuple):
            self.first = first[0]
            self.second = first[1]
            self.third = first[2]
    
    def __repr__(self):
        return "<%s.%s %s>" % (self.__module__, self.__class__.__name__, 
                                  str(self))

    def __str__(self):
        return "1:%s 2:%s 3:%s" % (self.first, self.second, self.third)
    
    def __iter__(self):
        self._iterindex = 0
        return self
    
    def __next__(self):
        i = self._iterindex
        if i >= 3:
            raise StopIteration        
        self._iterindex += 1
        return self[i]
    
    def next(self):
        return self.__next__()

    def __getitem__(self, k):
        try:
            if k < 0 or k > 2:
                raise IndexError('item must be between 0 and 2')
            if k == 0:
                return self.first
            elif k == 1:
                return self.second
            elif k == 2:
                return self.third
        except ValueError:           
            raise IndexError('item must be an int')
    
    def __setitem__(self, k, v):
        try:
            if k < 0 or k > 2:
                raise IndexError('item must be between 0 and 2')
            if k == 0:
                self.first = v
            elif k == 1:
                self.second = v
            elif k == 2:
                self.third = v
        except ValueError:           
            raise IndexError('item must be an int')

    def copy(self):
        return self.__class__(self.first, self.second, self.third, parent=self.parent)


class LineupCard(object):
    pass

class PlateAppearance(object):
    def __init__(self, abbreviation=None):
        self.abbreviation = abbreviation
        

class BoxScore(object):
    pass

class ExpectedRunMatrix(object):
    # http://www.baseballprospectus.com/sortable/index.php?cid=975409
    # 2011 MLB
    # (1st base occupied, 2nd occupied, 3rd occupied) : (0 outs, 1 out, 2 outs runs)
    expectedRunsDefault = { (False, False, False): (0.4807, 0.2582, 0.0967),
                            (False, False, True):  (1.3118, 0.899,  0.3545),
                            (False, True,  False): (1.0631, 0.6492, 0.3137),
                            (False, True,  True):  (1.8942, 1.29  , 0.5715),
                            (True,  False, False): (0.85  , 0.5026, 0.2174),
                            (True,  False, True):  (1.6811, 1.1434, 0.4752),
                            (True,  True,  False): (1.4324, 0.8936, 0.4344),
                            (True,  True,  True):  (2.2635, 1.5344, 0.6922),
                          }
    def __init__(self):
        self.expectedRuns = copy.copy(self.expectedRunsDefault)
        
    def runsForSituation(self, firstOccupied=False, secondOccupied=False, thirdOccupied=False, outs=0):
        '''
        >>> erm = ExpectedRunMatrix()
        >>> erm.runsForSituation(secondOccupied=True, outs=2)
        0.3137
        '''
        if outs >= 3:
            return 0.0
        return self.expectedRuns[firstOccupied, secondOccupied, thirdOccupied][outs]
    
if __name__ == '__main__':
    mainTest()