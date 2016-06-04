# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Name:         plateAppearance.py
# Purpose:      Represents a collection of Play events that make up a plateAppearance
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
#------------------------------------------------------------------------------
from daseki import common

class PlateAppearance(common.ParentMixin):
    '''
    Represents a plateAppearance (even one that should not count for OBP 
    such as Catcher's Interference) by the player and each 
    element in that list is itself a list of all Play objects representing that
    plate appearance as well as any substitutions or other events that take place during
    the PA.
    
    >>> g = game.Game('SDN201304090')
    >>> hi = g.halfInningByNumber(8, common.TeamNum.HOME)
    >>> pa0 = hi.plateAppearances[0]
    >>> pa0
    <daseki.plateAppearance.PlateAppearance 8-1: gyorj001:W>
    >>> pa0.events
    [<daseki.retro.play.Play b8: gyorj001:NP>, 
     <daseki.player.Sub visitor,8: Jerry Hairston (hairj002):thirdbase>, 
     <daseki.retro.play.Play b8: gyorj001:NP>, 
     <daseki.player.Sub visitor,9: Nick Punto (puntn001):shortstop>, 
     <daseki.retro.play.Play b8: gyorj001:W>]
   
    Most attributes of a Play event work on a plate appearance:
    
    >>> pa0.baseOnBalls
    True
    >>> pa0.runnersAfter
    <daseki.core.BaseRunners 1:gyorj001 2:False 3:False>
    
    Play indexes are stored:
    
    >>> pa0.startPlayNumber, pa0.endPlayNumber
    (83, 85)
    >>> pa0.inningNumber
    8
    >>> pa0.visitOrHome
    <TeamNum.HOME: 1>
    
    pitcherId is not yet implemented (TODO: Fix! 
    Decide: What should be the value for multiple
    pitchers/sub-mid-at-bat? Probably the pitcher of record)
    
    >>> pa0.batterId, pa0.pitcherId
    ('gyorj001', None)
    >>> pa0.outsBefore
    0
    >>> pa0.plateAppearanceInInning
    1
    
    This will be True if it ends with a substitution or a caught stealing play or
    something of that sort.  (TODO: Test)
    
    >>> pa0.isIncomplete
    False
    '''
    def __init__(self, *, parent=None):
        super().__init__(parent=parent)
        self.events = []
        self.startPlayNumber = -1
        self.endPlayNumber = -1
        self.inningNumber = None
        self.visitOrHome = common.TeamNum.VISITOR
        self.batterId = None
        self._pitcherId = None
        self.outsBefore = -1
        self.plateAppearanceInInning = 0
        self.isIncomplete = False # sub in the middle of the inning
        
    def append(self, e):
        self.events.append(e)

    def __getattr__(self, attr):
        le = self.lastPlayEvent
        if le is None:
            raise IndexError("'%s' object has events to search for attributes on" % 
                             (self.__class__.__name__,))
        if hasattr(le, attr):
            return getattr(le, attr)
        elif hasattr(le.playEvent, attr):
            return getattr(le.playEvent, attr)
        elif hasattr(le.runnerEvent, attr):
            return getattr(le.runnerEvent, attr)
        else:
            raise AttributeError("'%s' object has no attribute '%s'" % 
                                 (self.__class__.__name__, attr))
        
    
    @property
    def outsAfter(self):
        outs = 0
        for p in self.events:
            if p.record != 'play':
                continue
            outs += p.outsMadeOnPlay
        return self.outsBefore + outs
    
    @property
    def runnersBefore(self):
        '''
        returns the runner situation before the at bat.
        '''
    
    @property
    def lastPlayEvent(self):
        '''
        Returns the last event that is a "play" event 
        in the PlateAppearance -- generally the one that something happens
        in.
        
        Returns None if there is no play event.
        
        (self.events[-1] might not be a play event if there's an associated
        comment, but self.lastPlayEvent will be one).
        '''
        for i in range(len(self.events)):
            j = len(self.events) - (i+1)
            if self.events[j].record == 'play':
                return self.events[j]
        return None

    @property
    def battingOrder(self):
        '''
        >>> g = game.Game('SDN201304090')
        >>> hi = g.halfInningByNumber(8, common.TeamNum.HOME)
        >>> pa0 = hi.plateAppearances[0]
        >>> pa0.battingOrder
        5 
        '''
        g = self.parentByClass('Game')
        if g is None:
            return None
        p = g.playerById(self.batterId)
        if p is None:
            return None
        return p.battingOrder

    @property
    def countsTowardOBP(self):
        '''
        Does this plate appearance count towards on-base-percentage?
        True if
        '''
    
    @property
    def pitcherId(self):
        '''
        to be elaborated later...
        '''
        if self._pitcherId:
            return self._pitcherId
        else:
            return None
    
    @pitcherId.setter
    def pitcherId(self, value):
        self._pitcherId = value
    
    def __repr__(self):
        incomplete = ""
        if self.isIncomplete is True:
            incomplete = "(I)"

        return "<%s.%s %s-%s%s: %s:%s>" % (self.__module__, self.__class__.__name__, 
                          self.inningNumber, self.plateAppearanceInInning, incomplete,
                          self.batterId, 
                          self.lastPlayEvent.raw)

if __name__ == '__main__':
    from daseki import mainTest
    mainTest() #Test # TestSlow
