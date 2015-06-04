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


import copy
import sys

from testRunner import mainTest
#from exceptionsBB import BBBalkException


class Inning(object):
    def __init__(self, inningNumber = 1, awayHalf = None, homeHalf = None):
        self.inningNumber = inningNumber
        self.awayHalf = awayHalf
        self.homeHalf = homeHalf

class HalfInning(object):
    def __init__(self, inningNumber = 1, homeAway = 'away', startingBatterNumber = 1):
        self.inningNumber = inningNumber
        self.homeAway = homeAway
        self.startingBatterNumber = startingBatterNumber
        self.results = []

class LineupCard(object):
    pass

class PlateAppearance(object):
    def __init__(self, abbreviation=None):
        self.abbreviation = abbreviation
        
class Player(object):
    pass

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