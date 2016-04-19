# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         __init__.py
# Purpose:      Daseki -- A toolkit for computational baseball analysis 
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2014-15 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
#------------------------------------------------------------------------------
from __future__ import print_function
from __future__ import division


import copy

from daseki.test.testRunner import mainTest # @UnresolvedImport
from daseki import common
from daseki.common import TeamNum # @UnresolvedImport
from daseki.exceptionsDS import DasekiException


# class Inning(object):
#     def __init__(self, inningNumber = 1, visitorHalf = None, homeHalf = None):
#         self.inningNumber = inningNumber
#         self.visitorHalf = visitorHalf
#         self.homeHalf = homeHalf



class HalfInning(common.ParentType):
    '''
    >>> g = game.Game('SDN201304090')
    >>> hi = g.halfInningByNumber(8, common.TeamNum.HOME)
    >>> hi
    <daseki.base.HalfInning b8 plays:83-100 (SDN201304090)>
    >>> hi.inningNumber
    8
    >>> print(hi.visitOrHome)
    TeamNum.HOME
    '''
    __slots__ = ('inningNumber', 'visitOrHome', 'events', '_iterindex',
                 '_prev', '_following', 'startPlayNumber', 'endPlayNumber',
                 '_plateAppearances')
    def __init__(self, inningNumber = 1, visitOrHome = TeamNum.VISITOR, *, parent=None):
        super().__init__(parent=parent)
        self.inningNumber = inningNumber
        self.visitOrHome = visitOrHome
        self.events = []
        self._iterindex = 0
        self._prev = None
        self._following = None
        self.startPlayNumber = -1
        self.endPlayNumber = -1
        self._plateAppearances = []
    
    def __repr__(self):
        p = self.parent
        if p is not None and p.id is not None:
            gi = p.id
        else:
            gi = ""
            
        return "<%s.%s %s%s plays:%s-%s (%s)>" % (self.__module__, 
                                                  self.__class__.__name__, 
                                                  self.topBottom[0], 
                                                  self.inningNumber, 
                                                  self.startPlayNumber, 
                                                  self.endPlayNumber,
                                                  gi)


    @property
    def plateAppearances(self):
        '''
        >>> from pprint import pprint as pp
        
        >>> g = game.Game('SDN201304090')
        >>> hi = g.halfInningByNumber(8, common.TeamNum.HOME)
        >>> pp(hi.plateAppearances)        
        [<daseki.retro.play.PlateAppearance 8-1: gyorj001: 
            [<daseki.retro.play.Play b8: gyorj001:NP>, 
             <daseki.player.Sub visitor,8: Jerry Hairston (hairj002):thirdbase>, 
             <daseki.retro.play.Play b8: gyorj001:NP>, 
             <daseki.player.Sub visitor,9: Nick Punto (puntn001):shortstop>, 
             <daseki.retro.play.Play b8: gyorj001:W>]>,
         <daseki.retro.play.PlateAppearance 8-2: amara001: 
            [<daseki.retro.play.Play b8: amara001:PB.1-2>, 
             <daseki.retro.play.Play b8: amara001:W>]>,
         <daseki.retro.play.PlateAppearance 8-3: maybc001: 
            [<daseki.retro.play.Play b8: maybc001:NP>, 
             <daseki.player.Sub visitor,5: Matt Guerrier (guerm001):pitcher>, 
             <daseki.retro.play.Play b8: maybc001:14/SH/BG.2-3;1-2>]>,
         <daseki.retro.play.PlateAppearance 8-4: hundn001: 
            [<daseki.retro.play.Play b8: hundn001:FC6/G.3XH(62);2-3>]>,
         <daseki.retro.play.PlateAppearance 8-5: denoc001: 
            [<daseki.retro.play.Play b8: denoc001:S9/G.3-H;1-2>]>,
         <daseki.retro.play.PlateAppearance 8-6: cabre001: 
            [<daseki.retro.play.Play b8: cabre001:W.2-3;1-2>]>,
         <daseki.retro.play.PlateAppearance 8-7: venaw001: 
            [<daseki.retro.play.Play b8: venaw001:NP>, 
             <daseki.player.Sub visitor,5: Luis Cruz (cruzl001):thirdbase>, 
             <daseki.retro.play.Play b8: venaw001:NP>, 
             <daseki.player.Sub visitor,8: J.P. Howell (howej003):pitcher>, 
             <daseki.retro.play.Play b8: venaw001:T8/L.3-H;2-H;1-H>]>,
         <daseki.retro.play.PlateAppearance 8-8(I): thayd001: 
            [<daseki.retro.play.Play b8: thayd001:NP>, 
             <daseki.player.Sub home,3: Jesus Guzman (guzmj005):pinchhitter>]>,
         <daseki.retro.play.PlateAppearance 8-8: guzmj005: 
            [<daseki.retro.play.Play b8: guzmj005:W>]>,
         <daseki.retro.play.PlateAppearance 8-9: alony001: 
            [<daseki.retro.play.Play b8: alony001:S6/G.3-H;1-2>]>,
         <daseki.retro.play.PlateAppearance 8-10: gyorj001: 
            [<daseki.retro.play.Play b8: gyorj001:W.2-3;1-2>]>,
         <daseki.retro.play.PlateAppearance 8-11: amara001: 
            [<daseki.retro.play.Play b8: amara001:K>]>]
        '''
        from daseki.retro import play
        if any(self._plateAppearances):
            return self._plateAppearances

        thisPA = play.PlateAppearance(parent=self)
        thisPA.visitOrHome = self.visitOrHome
        thisPA.inningNumber = self.inningNumber
        thisPA.batterId = self.events[0].playerId
        thisPA.outsBefore = 0
        thisPA.plateAppearanceInInning = 1

        outsInInning = 0
        plateAppearanceInInning = 1
        thisPA.startPlayNumber = self.events[0].playNumber
        
        for i,p in enumerate(self.events):
            if p.record == 'play' and p.playerId != thisPA.batterId:
                thisPA.endPlayNumber = p.playNumber - 1
                self._plateAppearances.append(thisPA)
                
                if self.events[i - 1].record == 'sub':
                    # last PA ended with a sub -- this is the same PA
                    plateAppearanceInInning -= 1
                    thisPA.isIncomplete = True
                    
                plateAppearanceInInning += 1

                thisPA = play.PlateAppearance(parent=self)
                thisPA.startPlayNumber = p.playNumber
                thisPA.visitOrHome = self.visitOrHome
                thisPA.inningNumber = self.inningNumber
                thisPA.outsBefore = outsInInning
                thisPA.plateAppearanceInInning = plateAppearanceInInning
                thisPA.batterId = p.playerId

            if p.record == 'play':
                outsInInning += p.outsMadeOnPlay
            thisPA.append(p)


        thisPA.endPlayNumber = self.events[-1].playNumber
        self._plateAppearances.append(thisPA)

        return self._plateAppearances
            

    @property
    def topBottom(self):
        if self.visitOrHome == common.TeamNum.VISITOR:
            return "top"
        else:
            return "bottom"

    
    def _getPrev(self):
        '''
        Get or set the previous halfInning within the game.  Do not set to link between games.
        '''
        return common.unwrapWeakref(self._prev)

    def _setPrev(self, prev):
        self._prev = common.wrapWeakref(prev)
        
    prev = property(_getPrev, _setPrev)

    def _getFollowing(self):
        '''
        Get or set the following halfInning within the game.  Do not set to link between games.
        
        We do not use next to maintain Py2 compatibility with iterators.
        '''
        return common.unwrapWeakref(self._following)

    def _setFollowing(self, following):
        self._following = common.wrapWeakref(following)
        
    following = property(_getFollowing, _setFollowing)

        
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

    def next(self):
        return self.__next__()

    def __getitem__(self, k):
        return self.events[k]

    def subByNumber(self, pn):
        '''
        >>> g = game.Game('SDN201304090')
        >>> hi = g.halfInningByNumber(7, common.TeamNum.HOME)
        >>> hi
        <daseki.base.HalfInning b7 plays:65-76 (SDN201304090)>
        >>> hi.subByNumber(75)
        <daseki.player.Sub home,3: Tyson Ross (rosst001):pinchrunner>
        '''
        for p in self.events:
            if p.record == 'sub' and p.playNumber == pn:
                return p
        return None
    
    def playByNumber(self, pn):
        '''
        >>> g = game.Game('SDN201304090')
        >>> hi = g.halfInnings[0]
        >>> hi.startPlayNumber
        0
        >>> hi.endPlayNumber
        4
        >>> hi.playByNumber(2)
        <daseki.retro.play.Play t1: kempm001:K>
        '''
        for p in self.events:
            if p.record == 'play' and p.playNumber == pn:
                return p
        return None
    
    def lastPlay(self):
        '''
        return the last play of the half inning.  Useful for things
        like left-on-base.
        
        >>> g = game.Game('SDN201304090')
        >>> hi = g.halfInnings[0]
        >>> hi.lastPlay()
        <daseki.retro.play.Play t1: uribj002:12(3)3/GDP>
        '''
        for p in reversed(self.events):
            if p.record == 'play':
                return p
        raise DasekiException('No play in inning!')
    
    @property
    def leftOnBase(self):
        '''
        returns the number of people left on base at the end of
        the inning.
        
        >>> g = game.Game('SDN201304090')
        >>> hi = g.halfInnings[0]
        >>> hi.leftOnBase
        2
        >>> hi.lastPlay().runnersAfter
        <daseki.base.BaseRunners 1:gonza003 2:ellim001 3:False>
        '''
        p = self.lastPlay()
        ra = p.runnersAfter
        lob = 0
        for r in ra:
            if r not in (False, None):
                lob += 1
        return lob
    
    @property
    def runs(self):
        r = 0
        for p in self.events:
            if p.record == 'play':
                r += p.runnerEvent.runs
                
        return r
                


class BaseRunners(common.ParentType):
    '''
    A relatively lightweight object for dealing with baserunners.
    
    >>> br = base.BaseRunners(False, 'cuthbert', 'hamilton')
    >>> br
    <daseki.base.BaseRunners 1:False 2:cuthbert 3:hamilton>
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
    #@common.keyword_only_args('parent')
    def __init__(self, first=False, second=False, third=False, *, parent=None):
        super().__init__(parent=parent)
        self.first = first
        self.second = second
        self.third = third
        self._iterindex = 0
        if type(first) in (list, tuple):
            self.first = first[0]
            self.second = first[1]
            self.third = first[2]
    
    
    @property
    def play(self):
        '''
        >>> g = game.Game('SDN201304090')
        >>> hi = g.halfInningByNumber(7, common.TeamNum.HOME)
        >>> p = hi.events[2]
        >>> p
        <daseki.retro.play.Play b7: maybc001:NP>
        >>> brb = p.runnersBefore
        >>> brb
        <daseki.base.BaseRunners 1:False 2:False 3:False>
        >>> brb.play
        <daseki.retro.play.Play b7: maybc001:NP>
        >>> brb.play is p
        True
        >>> bra = p.runnersAfter
        >>> bra.play is p
        True
        '''
        return self.parentByClass('Play')
    
    def playerEntranceObjects(self):
        '''
        get PlayerEntrance objects for each baserunner or None if no baserunner.
        
        >>> g = game.Game('SDN201304090')
        >>> hi = g.halfInningByNumber(9, common.TeamNum.VISITOR)
        >>> p = hi.events[-1]
        >>> brb = p.runnersBefore
        >>> brb
        <daseki.base.BaseRunners 1:puntn001 2:False 3:False>
        >>> brb.playerEntranceObjects()
        [<daseki.player.Sub visitor,9: Nick Punto (puntn001):shortstop>, None, None]
        '''
        play = self.play
        if play is None:
            return None
        playNumber = play.playNumber
        visitOrHome = play.visitOrHome
        game = self.parentByClass('Game')
        if game is None:
            return None
        lc = game.lineupCards[visitOrHome]
        order = lc.battingOrderAtPlayNumber(playNumber)
        retObj = [None, None, None]
        for i in range(3):
            playerId = self[i]
            for j in order:
                if j is None: # batting order 0
                    continue
                if j.id == playerId:
                    retObj[i] = j
        return retObj
    
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




# class PlateAppearance(object):
#     def __init__(self, abbreviation=None):
#         self.abbreviation = abbreviation
#         
# 
# class BoxScore(object):
#     pass

class ExpectedRunMatrix(object):
    '''
    Represents the run situation for a given baserunning situation and number of outs.
    
    Numbers by default from 2011 MLB. 
    
    http://www.baseballprospectus.com/sortable/index.php?cid=975409    
    '''
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
        
    def runsForSituation(self, baseRunners, outs=0):
        '''
        >>> erm = base.ExpectedRunMatrix()
        >>> brr = base.BaseRunners(False, 'carmel', False)
        >>> erm.runsForSituation(brr, outs=2)
        0.3137
        '''
        if outs >= 3:
            return 0.0
        firstOccupied = False if baseRunners[0] in (False, None) else True
        secondOccupied = False if baseRunners[1] in (False, None) else True
        thirdOccupied = False if baseRunners[2] in (False, None) else True

        return self.expectedRuns[firstOccupied, secondOccupied, thirdOccupied][outs]
    
    def runsInherited(self, baseRunners, outs=0):
        '''
        Returns the difference between the runs expected for the current base/outs situation 
        and the runs expected for the same number of outs with no one on base.
        
        >>> erm = base.ExpectedRunMatrix()
        >>> brr = base.BaseRunners(False, 'nori', False)
        >>> erm.runsInherited(brr, outs=2)
        0.217
        '''
        return round(self.runsForSituation(baseRunners, outs) - 
                     self.runsForSituation((False, False, False), outs), 4)
    
    def runsInheritedNotOutAdjusted(self, baseRunners, outs=0):
        '''
        Returns the difference between the runs expected for the current base/outs situation and the 
        runs expected for NO OUTS with no one on base.
        
        >>> erm = base.ExpectedRunMatrix()
        >>> brr = base.BaseRunners(False, 'kate', False)
        >>> erm.runsInheritedNotOutAdjusted(brr, outs=2)
        -0.167
        '''
        return round(self.runsForSituation(baseRunners, outs) - 
                     self.runsForSituation((False, False, False), 0), 4)

    def simpleRunsExpected(self, baseRunners, outs=0):
        '''
        returns the very simple, but pretty accurate, run expectation given in my blog post
        http://prolatio.blogspot.com/2008/08/hate-stat-love-statter.html using the formula:
        
        ::
        
            ER = (5 + total_runners + 3 * (total bases occupied))  * outs_left / 30
        
        
        >>> erm = base.ExpectedRunMatrix()
        >>> brr = base.BaseRunners(False, False, False)
        >>> erm.simpleRunsExpected(brr, 0)
        0.5
        
        >>> for third in (False, True):
        ...     for second in (False, True):
        ...         for first in (False, True):
        ...             for outs in range(3):
        ...                 brr = base.BaseRunners(first, second, third)
        ...                 sre = erm.simpleRunsExpected(brr, outs)
        ...                 re = erm.runsForSituation(brr, outs)
        ...                 print("{0:5s} {1:5s} {2:5s} {3} {4:4.2f} {5:4.2f} {6:4.2f}".format(
        ...                     str(first), str(second), str(third), 
        ...                     outs, sre, re, sre - re))
        False False False 0 0.50 0.48 0.02
        False False False 1 0.33 0.26 0.08
        False False False 2 0.17 0.10 0.07
        True  False False 0 0.90 0.85 0.05
        True  False False 1 0.60 0.50 0.10
        True  False False 2 0.30 0.22 0.08
        False True  False 0 1.20 1.06 0.14
        False True  False 1 0.80 0.65 0.15
        False True  False 2 0.40 0.31 0.09
        True  True  False 0 1.60 1.43 0.17
        True  True  False 1 1.07 0.89 0.17
        True  True  False 2 0.53 0.43 0.10
        False False True  0 1.50 1.31 0.19
        False False True  1 1.00 0.90 0.10
        False False True  2 0.50 0.35 0.15
        True  False True  0 1.90 1.68 0.22
        True  False True  1 1.27 1.14 0.12
        True  False True  2 0.63 0.48 0.16
        False True  True  0 2.20 1.89 0.31
        False True  True  1 1.47 1.29 0.18
        False True  True  2 0.73 0.57 0.16
        True  True  True  0 2.60 2.26 0.34
        True  True  True  1 1.73 1.53 0.20
        True  True  True  2 0.87 0.69 0.17
        '''
        firstOccupied = 0 if baseRunners[0] in (False, None) else 1
        secondOccupied = 0 if baseRunners[1] in (False, None) else 1
        thirdOccupied = 0 if baseRunners[2] in (False, None) else 1

        totalBasesOccupied = firstOccupied + 2 * secondOccupied + 3 * thirdOccupied
        totalRunners = firstOccupied + secondOccupied + thirdOccupied
        outsLeft = 3 - outs
        erexp = (5 + totalRunners + 3 * totalBasesOccupied) * outsLeft/30.0
        return erexp


if __name__ == '__main__':
    mainTest()
