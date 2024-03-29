# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         play.py
# Purpose:      retrosheet Play event
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015-22 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
The most important, but also the most complex Retrosheet field,
a play represents a single play
in a game.  An example play could be as simple as:

    play,2,1,lemkm001,12,BCSS,K

Which means that in the second inning, home half (1),
the player "lemkm001", after a 1-2 count,
with pitches "ball, called strike, strike swinging, strike swinging",
struck out (K).

Or it could be as complex as:

    play,7,0,mcrab001,12,FF*BX,S9/L34D/R932/U1.2-H;1-H(E3/TH)(UR)(NR);B-2

Which I won't describe here!  :-)

Notice in both these cases, it is the last column in the
csv entry that contains all the
information about the outcome of the play.  This information will be parsed and
stored in the RunnerEvent and PlayEvent objects associated with each Play object.
'''
import re
from typing import Callable, Any

DEBUG = False

NON_ERROR_PAREN_THROW_RE = re.compile(r'\(\d+/?T?H?\)')
ERROR_PAREN_RE = re.compile(r'\(\d*E\d*[/A-Z]*\)')
ERROR_RE = re.compile(r'\d*E\d*[/A-Z]*')

from daseki.retro import datatypeBase
from daseki import common
from daseki.exceptionsDS import RetrosheetException
from daseki.common import warn
from daseki import core


class PlayParseException(RetrosheetException):
    pass


class Play(datatypeBase.RetroData):
    '''
    The most important and most complex record: records a play.

    The playEvent potentially has two main sections separated by "." -- the PlayEvent
    (batter information) and optionally the RunnerEvent (showing changes of bases because
    of errors, advancing on throws, etc.).


    Tough one:

    >>> from daseki import retro
    >>> p = retro.play.Play(playerId='batter', raw='54(1)/FO/G/DP.3XH(42)')
    >>> p.runnersBefore = core.BaseRunners('A', False, 'C')
    >>> p.outsMadeOnPlay
    2
    >>> p.playEvent
    <daseki.retro.play.PlayEvent 54(1)/FO/G/DP>
    >>> p.playEvent.isDblPlay
    True
    >>> p.runnerEvent
    <daseki.retro.play.RunnerEvent 3XH(42) (1:A 2:False 3:C) -> (1:batter 2:False 3:False)>
    >>> p.runnersAdvance
    [<daseki.retro.play.RunnerAdvance 3XH(42)>,
     <daseki.retro.play.RunnerAdvance 1X2>,
     <daseki.retro.play.RunnerAdvance B-1>]
    '''
    __slots__ = ('inning', 'visitOrHome', 'playerId', 'count', '_pitches', 'raw',
                 '_playEvent', '_runnerEvent', 'runnersBefore', 'runnersAfter',
                 'rawBatter', 'rawRunners',)

    record = 'play'
    visitorNames = ['visitor', 'home']

    def __init__(self,
                 inning=0,
                 visitOrHome=0,
                 playerId='',
                 count='',
                 pitches='',
                 raw='',
                 *,
                 parent=None):
        super().__init__(parent=parent)
        self.inning = int(inning)
        self.visitOrHome = int(visitOrHome)  # 0 = visitor, 1 = home
        self.playerId = playerId
        self.count = count
        self._pitches = pitches
        self.raw = raw
        self._playEvent = None
        self._runnerEvent = None

        self.runnersBefore = None   # , False, (True or a batterId)
        self.runnersAfter = None  # None, False, (True or a batterId)

        rs = self.raw.split('.', 1)
        self.rawBatter = rs[0]
        if len(rs) > 1:
            self.rawRunners = rs[1]
        else:
            self.rawRunners = None

    def __repr__(self):
        return '<%s.%s %s%s: %s:%s>' % (self.__module__,
                                        self.__class__.__name__,
                                        self.topBottom[0],
                                        self.inning,
                                        self.playerId,
                                        self.raw)

    @property
    def runnersAdvance(self):
        return self.runnerEvent.runnersAdvance

    @property
    def visitorName(self):
        return self.visitorNames[int(self.visitOrHome)]

    @property
    def rbis(self):
        '''
        give the number of RBIs made on the play.  Usually 0

        >>> from daseki import retro
        >>> p = retro.play.Play(
        ...       playerId='mcrab001',
        ...       raw='S9/L34D/R932/U1.2-H;1-H(E3/TH)(UR)(NR);B-2')
        >>> p.rbis
        1
        '''
        ra = self.runnerEvent.runnersAdvance
        if ra is None:
            return 0
        rbis = 0
        for oneRa in ra:
            if oneRa.isRBIInferred:
                rbis += 1
        return rbis

    @property
    def outsMadeOnPlay(self):
        '''
        >>> from daseki import retro
        >>> p = retro.play.Play(raw='K+CS2(26)/DP')
        >>> p.playEvent.isOut
        True
        >>> p.outsMadeOnPlay
        2

        >>> p = retro.play.Play(raw='K+WP.B-1')
        >>> p.outsMadeOnPlay
        0

        Note that the runner "isOut" because of the strikeOut even though
        outsMadeOnPlay is 0:

        >>> p.playEvent.isOut
        True



        There could be outs made on the play even where playEvent.isOut is False
        because the batter could single and be out stretching to a double:

        (from the 1934 ASG t7 gehrc101)

        >>> from daseki import retro
        >>> p = retro.play.Play(raw='S9.BX2(96)')
        >>> p.playEvent.isOut
        False
        >>> p.outsMadeOnPlay
        1

        '''
        # decently complex because of strikeout caught stealing
        #     / strikeout wild pitch out
        # if explicitly coded, use this...
        if self.playEvent.isDblPlay:
            return 2
        if self.playEvent.isTplPlay:
            return 3
        outs = 0
        if self.playEvent.isOut:
            outs += 1
            if self.playEvent.strikeOut is True and self.runnerEvent.hasRunnerAdvance('B'):
                outs -= 1
        outs += self.runnerEvent.outs
        return outs

    @property
    def topBottom(self):
        if self.visitOrHome == common.TeamNum.VISITOR:
            return 'top'
        else:
            return 'bottom'

    @property
    def runnerEvent(self):
        if self._runnerEvent is not None:
            return self._runnerEvent
        # pylint: disable=broad-except
        try:
            revt = self.getRunnerEvent()
            revt.parse()
        except Exception as exc:
            raise PlayParseException(
                f'RunnerEvent error in {self!r}: {exc}'
            ) from exc
        return self._runnerEvent

    @property
    def playEvent(self):
        if self._playEvent is not None:
            return self._playEvent

        # pylint: disable=broad-except
        try:
            play_evt = self.getPlayEvent()
            play_evt.parse()
        except Exception as exc:
            raise PlayParseException(
                f'PlayEvent error in {self!r}: {exc}'
            ) from exc
        return self._playEvent

    def getPlayEvent(self):
        self._playEvent = PlayEvent(self.rawBatter, parent=self)
        return self._playEvent

    def getRunnerEvent(self):
        self._runnerEvent = RunnerEvent(self.rawRunners, self.runnersBefore, parent=self)
        # warn(self._runnerEvent.parent, ' is the parent')
        return self._runnerEvent


class RunnerAdvance():
    '''
    Characterizes a single runner advance event.

    Not a Parent mixin, because of slowness...
    '''
    __slots__ = ('_raw', 'afterMods', 'playerId', 'isImplied',
                 'baseBefore', 'baseAfter', 'isOut', 'numErrors', 'errorPositions',)

    REDUNDANT_STRIP = re.compile(r'\(\dX\)$')

    def __init__(self, raw='', playerId=None):  # , *, parent=None):
        # super().__init__(parent=parent)
        # self.superRaw = None # see setRaw
        self._raw = None
        self.afterMods = None
        self.playerId = playerId
        self.isImplied = False
        self.baseBefore = None
        self.baseAfter = None
        self.isOut = False
        self.numErrors = 0
        self.errorPositions = None

        self.raw = raw


    def __repr__(self):
        return f'<{self.__module__}.{self.__class__.__name__} {self.raw}>'


    def _getRaw(self):
        return self._raw

    def _setRaw(self, raw):
        # self.superRaw = raw  # save redundant info? probably not...
        if '(' in raw:
            raw = self.REDUNDANT_STRIP.sub('', raw)
        # very few cases of 2X3(1X) such as COL200205190; redundant
        self._raw = raw
        if '-' in raw:
            before, after = raw.split('-')
            self.isOut = False
        elif 'X' in raw:
            before, after = raw.split('X')
            self.isOut = True
        else:
            raise RetrosheetException(f'Something wrong with runner: {raw}')

        self.baseBefore = before[0]
        # 'Base' refers to the first letter/number which identifies the baserunner.
        # beforeMods = before[1:]
        self.baseAfter = after[0]
        afterMods = after[1:]
        if ERROR_PAREN_RE.search(afterMods):
            # error occurred, do not mark out...
            # unless there is also a non-error throw marked
            self.numErrors += 1
            # TODO: Record who made the error!
            if not NON_ERROR_PAREN_THROW_RE.search(afterMods):
                self.isOut = False
                # turns out occasionally the 1XH(E7) is still an out, but with an error.

        if afterMods != '':
            self.afterMods = afterMods

    raw = property(_getRaw, _setRaw)

    def sortKey(self):
        '''
        helper function so that events beginning on 3rd sort first,
        then 2nd, then 1st, then B (batter).
        That way, say you have 1-3,3XH, the events get sorted as
        3XH (runner on third out at home)
        then 1-3 (runner on first goes to third), rather than runner
        on 1st goes to 3rd and then thrown
        out at home.

        Handles a few strange sorting moments, such as Segura's "advance"
        from 2nd to 1st in April 2013.
        Put any similar events here.
        '''
        if self.baseBefore == '3':
            return 'A'
        elif self.baseBefore == '2':
            if self.baseAfter == '1':
                # Just for Segura, Milwaukee 19 April 2013 --
                #    Segura steals second then runs back to first
                # https://www.youtube.com/watch?v=HZM1JcJwo9E
                # sort last...
                return 'X'
            else:
                return 'B'
        elif self.baseBefore == '1':
            return 'C'
        elif self.baseBefore == 'B':
            return 'D'
        else:
            raise RetrosheetException(
                f'Unknown rEvt for sorting: {self.raw}, {self.baseBefore}')
            # return 'Z' + self.raw


    @property
    def isRun(self):
        if self.baseAfter == 'H':
            return True
        else:
            return False

    @property
    def isUnearnedRunExplicit(self):
        if '(UR)' in self.raw:
            return True
        else:
            return None

    @property
    def isRBIExplicit(self):
        if '(RBI)' in self.raw:
            return True
        if '(NR)' in self.raw or '(NORBI)' in self.raw:
            return False
        return None

    @property
    def isEarnedRun(self):
        if self.isRun is not True:
            return False
        if self.isUnearnedRunInferred is True:
            return False
        return True

    @property
    def isUnearnedRunInferred(self):
        explicit = self.isUnearnedRunExplicit
        if explicit is not None:
            return explicit
        if self.baseAfter is not 'H':
            return False
        return False

    @property
    def isRBIInferred(self):
        rae = self.isRBIExplicit
        if rae is not None:
            return rae
        if self.baseAfter == 'H':
            return True
        else:
            return False


class RunnerEvent(common.ParentMixin):
    '''
    An object that, given the information from a Play object and a list of runners before the event
    can figure out who is on each base after the event.

    Needs a reference to the parent Play object to look at the Play object's PlayEvent which
    contains information about stolenBases etc.
    '''
    __slots__ = ('runnersBefore', 'runnersAfter', 'runnersAdvance',
                 'outs', 'runs', 'scoringRunners', 'raw',)

    def __init__(self, raw='', runnersBefore=None, *, parent=None):
        super().__init__(parent=parent)
        self.raw = raw
        if runnersBefore is not None:
            self.runnersBefore = runnersBefore
        else:
            self.runnersBefore = core.BaseRunners(False, False, False)  # , parent=self)

        self.runnersAfter = None
        self.runnersAdvance = None
        self.outs = 0
        self.runs = 0
        self.scoringRunners = []
        if DEBUG:
            print(runnersBefore)

    def __repr__(self):
        return '<%s.%s %s (%s) -> (%s)>' % (self.__module__,
                                            self.__class__.__name__,
                                            self.raw,
                                            self.runnersBefore,
                                            self.runnersAfter
                                            )


    def parse(self):
        '''
        Parse the runnerEvent's .raw attribute and set runnerAdvance.
        '''
        raw = self.raw
        if raw is not None and raw != '':
            ra = [RunnerAdvance(x) for x in raw.split(';')]
        else:
            ra = []
        self.runnersAdvance = ra

        try:
            pe = self.parent.playEvent
        except AttributeError:
            # warn('No parent.playEvent!')
            return  # no parent.playEvent
        self.updateRunnersAdvanceBasedOnPlayEvent(pe)
        self.setRunnersAfter(runnersAdvanceList=ra)

    def setRunnersAfter(self, runnersAdvanceList=None):
        '''
        Consults the runnersAdvanceList and runnersBefore to set the names of runners afterwards.

        also sets the number of outs and number of runs.

        >>> from daseki import retro
        >>> RA = retro.play.RunnerAdvance
        >>> runnerAdvances = [RA('1-2'), RA('3XH')]
        >>> runnersBefore = core.BaseRunners('michael', False, 'jennifer')

        >>> revt = retro.play.RunnerEvent()
        >>> revt.runnersBefore = runnersBefore
        >>> runAfter = revt.setRunnersAfter(runnerAdvances)
        >>> runAfter is revt.runnersAfter
        True
        >>> runAfter
        <daseki.core.BaseRunners 1:False 2:michael 3:False>
        >>> revt.outs
        1

        >>> runnerAdvances = [RA('B-1'), RA('1-2'), RA('3-H(UR)')]
        >>> runnersBefore = core.BaseRunners('michael', False, 'jennifer')

        >>> revt = retro.play.RunnerEvent()
        >>> revt.runnersBefore = runnersBefore
        >>> runAfter = revt.setRunnersAfter(runnerAdvances)
        >>> runAfter
        <daseki.core.BaseRunners 1:unknownBatter 2:michael 3:False>
        >>> revt.outs
        0
        >>> revt.runs
        1
        >>> revt.scoringRunners
        ['jennifer']

        >>> revt = retro.play.RunnerEvent(raw='B-1;1X3;3-H')
        >>> revt.parse()
        >>> revt.runnersBefore = ['michael', False, 'jennifer']
        >>> revt.setRunnersAfter()
        ['unknownBatter', False, False]
        >>> revt.runs
        1
        '''
        if runnersAdvanceList is None:
            runnersAdvanceList = self.runnersAdvance

        self.runnersAfter = self.runnersBefore.copy()
        # in case of implied advances, we may get the same data twice.
        alreadyTakenCareOf = [False, False, False, False]  # batter, first, second, third...

        # process 3rd first, then second, then first, then batter...
        for raObj in sorted(runnersAdvanceList, key=lambda x: x.sortKey()):
            self.handleOneRunnerAdvanceObject(raObj, alreadyTakenCareOf)

        parent = self.parent
        if parent is not None:
            parent.runnersAfter = self.runnersAfter
        return self.runnersAfter

    def handleOneRunnerAdvanceObject(self, raObj, alreadyTakenCareOf=None):
        '''
        Sets self.runnersBefore and self.runnersAfter based on one RunnerAdvance
        object along with the number of outs and runs on account of this
        runner:

        >>> from daseki import retro
        >>> revt = retro.play.RunnerEvent(raw='B-1;1X3;3-H')
        >>> revt.parse()
        >>> revt.runnersBefore = ['michael', False, 'jennifer']
        >>> revt.runnersAfter = ['michael', False, 'jennifer']
        >>> revt.setRunnersAfter()
        ['unknownBatter', False, False]
        >>> revt.runs
        1
        '''
        if alreadyTakenCareOf is None:
            alreadyTakenCareOf = [False, False, False, False]

        isOut = raObj.isOut
        baseBefore = raObj.baseBefore
        baseAfter = raObj.baseAfter

        runnersBefore = self.runnersBefore
        runnersAfter = self.runnersAfter

        if baseBefore in ('1', '2', '3'):
            beforeInt = int(baseBefore)
            # check to see if this has already been taken care of.  Sometimes we have
            # both an explicit and an implicit runner advance.
            if alreadyTakenCareOf[beforeInt] is True:
                return
            runnerIdOrFalse = runnersBefore[beforeInt - 1]
            alreadyTakenCareOf[beforeInt] = True
            raObj.playerId = runnersBefore[beforeInt - 1]
            runnersAfter[beforeInt - 1] = False  # assumes proper encoding order of advancement
        elif baseBefore == 'B':
            if alreadyTakenCareOf[0] is True:
                return  # implied batter but also given explicitly
            parent = self.parent
            if parent is not None:
                runnerIdOrFalse = parent.playerId
            else:
                runnerIdOrFalse = 'unknownBatter'
            alreadyTakenCareOf[0] = True
        else:
            raise RetrosheetException('Runner Advance without a base!: %s: %s: %s' %
                                      (raObj, self.raw, self.parent.raw))


        if isOut is False:
            if runnerIdOrFalse is False:
                warn('\n****\nError about to occur!')
                warn(f'it is in Inning {self.parent.inning}')
                warn(self.runnersAdvance)
                warn(runnersBefore)
                warn(runnersAfter)
                warn(self.parent.parent.id)
                pass  # debug

            if baseAfter in ('1', '2', '3'):
                runnersAfter[int(baseAfter) - 1] = runnerIdOrFalse
                if DEBUG:
                    print(runnerIdOrFalse + ' goes to ' + common.ordinals[int(baseAfter)])
            elif baseAfter == 'H':
                self.scoringRunners.append(runnerIdOrFalse)
                if DEBUG:
                    print(f'{runnerIdOrFalse} scores!')
                self.runs += 1
            else:
                raise RetrosheetException('Runner Advanced but to WHERE?: %s: %s: %s' %
                                          (baseAfter, self.raw, self.parent.raw))

        else:  # out is made...
            if runnerIdOrFalse is False:
                print('\n****\n'
                      'Error about to occur -- someone is out but we do not know who!')
                print(f'it is in Inning {str(self.parent.inning)}: '
                      f'{str(self.parent.visitOrHome)}')
                print(self.runnersAdvance)
                print(runnersBefore)
                print(runnersAfter)
                if self.parent is not None and self.parent.parent is not None:
                    print(self.parent.parent.id)
                pass  # debug
            if DEBUG:
                print(f'{runnerIdOrFalse} is out')
            self.outs += 1


    def updateRunnersAdvanceBasedOnPlayEvent(self, playEvent=None):
        '''
        .runnersAdvance is a list of advances by runners on each base.

        It is initially populated by information from the running information
        given after the period in the event list, but there are a lot of cases
        where the main event has implied runner advances (stolen bases, etc.),
        so we look at the playEvent (generally in the Play object's playEvent attribute)
        to see what to update here.
        '''
        if playEvent is None:
            playEvent = self.parent.playEvent
        raList = self.runnersAdvance

        if playEvent.basesStolen is not None:
            for b in playEvent.basesStolen:  # do not check (if playEvent.stolenBase)
                # because CS(E4) can mean there is a base stolen without a stolen base
                ra = None
                if b == 'H' and not self.hasRunnerAdvance('3'):
                    ra = RunnerAdvance('3-H', playerId=self.runnersBefore.third)
                elif b == '3' and not self.hasRunnerAdvance('2'):
                    ra = RunnerAdvance('2-3', playerId=self.runnersBefore.second)
                elif b == '2' and not self.hasRunnerAdvance('1'):
                    ra = RunnerAdvance('1-2', playerId=self.runnersBefore.first)
                if ra is not None:
                    raList.append(ra)

        if playEvent.eraseBaseRunners is not None:
            for b in playEvent.eraseBaseRunners:
                ra = None

                if b == '1' and not self.hasRunnerAdvance('1'):
                    ra = RunnerAdvance('1X2', playerId=self.runnersBefore.first)
                elif b == '2' and not self.hasRunnerAdvance('2'):
                    ra = RunnerAdvance('2X3', playerId=self.runnersBefore.second)
                elif b == '3' and not self.hasRunnerAdvance('3'):
                    ra = RunnerAdvance('3XH', playerId=self.runnersBefore.third)
                if ra is not None:
                    raList.append(ra)

        if not self.hasRunnerAdvance('B') and playEvent.impliedBatterAdvance != 0:
            # if we do not already have information on the batter advance then
            # look for it in the play event
            iba = playEvent.impliedBatterAdvance
            if iba in (1, 2, 3):
                bEvent = 'B-' + str(iba)
            elif iba == 4:
                bEvent = 'B-H'
            else:
                raise RetrosheetException(
                    f'Huh??? Implied batter advance ({iba}) is strange')
            ra = RunnerAdvance(bEvent, playerId=self.parent.playerId)
            ra.isImplied = True
            raList.append(ra)

    def hasRunnerAdvance(self, letter: str|int) -> bool:
        '''
        Takes in a letter (or int) representing a base that may have a runner ("1", "2", "3")
        and returns True or False about whether a runner has advanced (or is out trying to advance,
        including required advances such as force outs) from that base.

        >>> from daseki import retro
        >>> revt = retro.play.RunnerEvent(raw='B-1;1X3;3-H')
        >>> revt.parse()
        >>> revt.hasRunnerAdvance('1')
        True
        >>> revt.hasRunnerAdvance(1)
        True
        >>> revt.hasRunnerAdvance('B')
        True
        >>> revt.hasRunnerAdvance('2')
        False
        '''
        if isinstance(letter, int):
            letter = str(letter)
        # warn('Runners advance:', self.runnersAdvance)
        for r in self.runnersAdvance:
            if r.baseBefore == letter:
                return True
        return False


class PlayEvent(common.ParentMixin):
    '''
    Definitely the most complex single parsing job. What actually happened in the play, from
    the batter's perspective
    '''
    __slots__ = ('raw', 'isOut', 'basicBatter',  'isSafe',
                 'isAtBat', 'isPlateAppearance',
                 'isNoPlay', 'fielders', 'impliedBatterAdvance', 'single',
                 'double', 'triple',
                 'doubleGroundRule', 'homeRun', 'strikeOut',
                 'baseOnBalls', 'baseOnBallsIntentional',
                 'errors', 'fieldersChoice', 'hitByPitch', 'totalBases', 'stolenBase',
                 'caughtStealing', 'basesStolen', 'eraseBaseRunners',
                 'isPickoff', 'isBalk', 'isPassedBall', 'isWildPitch',
                 'isDblPlay', 'isTplPlay', 'modifiers', 'defensiveIndifference',
                 'ignoreForOBP',
                 'isSacrificeFly', 'isSacrificeHit',)

    def __init__(self, raw='', *, parent=None):
        super().__init__(parent)
        self.isOut = False  # is the batter out on the play
        self.basicBatter = None
        self.isSafe = False  # ??? in case of, say, a SB play, etc., both can be False
        self.fielders = tuple()

        self.impliedBatterAdvance = 0
        # number of bases implied for the batter's single, double, etc.

        self.single = False
        self.double = False
        self.doubleGroundRule = False
        self.triple = False
        self.homeRun = False

        self.strikeOut = False
        self.baseOnBalls = False
        self.baseOnBallsIntentional = False

        self.errors = 0
        self.fieldersChoice = False
        self.hitByPitch = False

        self.isAtBat = True
        self.isPlateAppearance = True
        self.isNoPlay = False

        self.totalBases = 0

        self.stolenBase = False  # a base was stolen (for statistical purposes)
        self.caughtStealing = False
        self.basesStolen = None
        self.eraseBaseRunners = None

        self.isPickoff = False
        self.isBalk = False
        self.isPassedBall = False
        self.isWildPitch = False

        self.isDblPlay = False
        self.isTplPlay = False
        self.modifiers = []
        self.defensiveIndifference = False
        self.ignoreForOBP = False  # rare: Catcher's Interference, Fielder's obstruction

        self.isSacrificeFly = False
        self.isSacrificeHit = False

        self.raw = raw

    def __repr__(self):
        return f'<{self.__module__}.{self.__class__.__name__} {self.raw}>'

    def parse(self):
        raw = self.raw
        self.splitBasicBatterModifiers(raw)
        self.parseBasicBatter(self.basicBatter)
        self.parseModifiers()

    def parseBasicBatter(self, bb=None):
        '''
        Runs through the matching methods of self.parseMethodOrder until
        one matches and then returns.
        '''
        if bb is None:
            bb = self.basicBatter

        matchMethod: Callable[['PlayEvent', Any], Any]
        for matchMethod in self.parseMethodOrder:
            if matchMethod(self, bb):
                return
        raise RetrosheetException(f'did not parse {bb}')

    def parseModifiers(self, modifiers=None):
        '''
        change the playEvent according to the modifiers -- the
        only ones that we look at now are sacrifice flies (SF)
        and sacrifice hits (SH).

        >>> from daseki import retro
        >>> pe = retro.play.PlayEvent()
        >>> pe.isAtBat = True
        >>> pe.parseModifiers(['SF', 'Odd Modifier'])
        >>> pe.isSacrifice
        True
        >>> pe.isSacrificeFly
        True
        >>> pe.isAtBat
        False
        '''
        if modifiers is None:
            modifiers = self.modifiers
        for thisMod in modifiers:
            if thisMod.startswith('SH'):
                self.isAtBat = False
                self.isSacrificeHit = True
            elif thisMod.startswith('SF'):
                self.isAtBat = False
                self.isSacrificeFly = True

    @property
    def isHit(self):
        '''
        returns True if this play counts as a hit.

        False doesn't mean it counts against the BA.  Only if isAtBat is True
        and isHit is False should it count that way.
        '''
        if self.single or self.double or self.triple or self.homeRun:
            return True
        else:
            return False

    @property
    def isSacrifice(self):
        '''
        returns True if the play is either a sacrificeFly or a sacrificeHit
        '''
        return (self.isSacrificeFly or self.isSacrificeHit)

    def matchStrikeout(self, bb):
        '''
        returns True if bb matches a strike out. Also checks for afterEvents:

        >>> from daseki import retro
        >>> pe = retro.play.PlayEvent()
        >>> pe.matchStrikeout('K')
        True
        >>> pe.strikeOut
        True
        >>> pe.isOut
        True

        After event:

        >>> pe = retro.play.PlayEvent()
        >>> pe.matchStrikeout('K+SB2')
        True
        >>> pe.strikeOut
        True
        >>> pe.isOut
        True
        >>> pe.stolenBase
        True
        >>> pe.basesStolen
        ['2']


        >>> pe = retro.play.PlayEvent()
        >>> pe.matchStrikeout('K+WP')
        True
        >>> pe.strikeOut
        True
        >>> pe.isOut # ???
        True


        # TODO - should isOut be False if afterEvent matches WP?
        '''
        if bb.startswith('K'):
            self.strikeOut = True
            self.isOut = True
            afterEvent = re.match(r'K\d*\+(.*)', bb)
            if afterEvent:
                # event after strike out...
                afterBB = afterEvent.group(1)
                self.parseBasicBatter(afterBB)
                # K+event -- strike out but not out...
            return True
        return False

    def matchBaseOnBalls(self, bb):
        '''
        returns True if bb matches a strike out. Also checks for afterEvents:

        >>> from daseki import retro
        >>> pe = retro.play.PlayEvent()
        >>> pe.matchBaseOnBalls('W')
        True
        >>> pe.baseOnBalls
        True
        >>> pe.baseOnBallsIntentional
        False

        >>> pe = retro.play.PlayEvent()
        >>> pe.matchBaseOnBalls('WP')
        False


        After event:

        >>> pe = retro.play.PlayEvent()
        >>> pe.matchBaseOnBalls('IW+SB3')
        True
        >>> pe.baseOnBalls
        True
        >>> pe.baseOnBallsIntentional
        True
        >>> pe.stolenBase
        True
        >>> pe.basesStolen
        ['3']
        '''
        if (bb.startswith('W') and
                not bb.startswith('WP') or
                bb.startswith('IW') or
                bb.startswith('I')):
            # "I" is older style intentional walk encoding, seen a lot before 1997.
            self.baseOnBalls = True
            matchCode = 'W'
            if bb.startswith('IW') or bb.startswith('I'):
                self.baseOnBallsIntentional = True
                matchCode = 'IW?'
            self.isSafe = True
            self.isAtBat = False
            self.impliedBatterAdvance = 1
            afterEvent = re.match(matchCode + r'\d*\+(.*)', bb)
            if afterEvent:
                # event after walk... continue...
                afterBB = afterEvent.group(1)
                self.parseBasicBatter(afterBB)
            return True
        return False

    def matchNoPlay(self, bb):
        '''
        No play:

        >>> from daseki import retro
        >>> pe = retro.play.PlayEvent()
        >>> pe.isAtBat # default
        True
        >>> pe.isPlateAppearance # default
        True
        >>> pe.isNoPlay # default
        False
        >>> pe.matchNoPlay('K')
        False
        >>> pe.matchNoPlay('NP')
        True
        >>> pe.isAtBat
        False
        >>> pe.isPlateAppearance
        False
        >>> pe.isNoPlay
        True
        '''
        if bb.startswith('NP'):
            self.isAtBat = False
            self.isPlateAppearance = False
            self.isNoPlay = True
            return True
        return False

    def matchGeneralOut(self, bb):
        '''
        Most common play: a ground or flyout to a position, given by number.

        Can affect attributes: isOut, impliedBatterAdvance, fielders, eraseBaseRunners, isDblPlay,
        isTplPlay, isSafe.
        '''
        out = re.match(r'(\d+)', bb)
        if out:
            safeOnError = ERROR_RE.search(bb)
            if safeOnError:
                self.isOut = False  # but out for statistics...
                self.impliedBatterAdvance = 1
            else:
                self.isOut = True
                self.fielders = tuple(out.group(1))
                numForced = 0
                for forces in re.finditer(r'\((\d)\)', bb):
                    # could be B also... but that is caught below
                    if DEBUG:
                        print(forces.group(1) + ' FORCE OUT')
                    numForced += 1
                    self.isOut = False  # batter is not out... unless GDP or something
                    if self.eraseBaseRunners is None:
                        self.eraseBaseRunners = []
                    self.eraseBaseRunners.append(forces.group(1))
                if numForced > 0:
                    isDblPlay = False
                    isTplPlay = False
                    for m in self.modifiers:
                        if 'DP' in m and 'NDP' not in m:
                            # includes 'BGDP' for bunted into double play
                            isDblPlay = True
                            # BPDP, DP (unspecified), FDP, GDP, LDP,
                            #    but not NDP (No double play)
                        if 'TP' in m and 'NTP' not in m:
                            # NTP does not exist in retrosheet but it could?
                            isTplPlay = True
                            isDblPlay = False  # MIL201108150 - t2: 46(1)3(B)/GDP/TP.2XH(32)
                    if isDblPlay is False and isTplPlay is False:
                        self.impliedBatterAdvance = 1
                        self.isSafe = True
                    elif isDblPlay is True and numForced == 2:
                        self.impliedBatterAdvance = 1  # he is safe!
                        self.isSafe = True
                    elif isDblPlay is True and numForced == 1:
                        # we need to check to see if in the runner events there is a non-force out
                        # throw as in top 1st: COL201407130
                        rr = self.parent.rawRunners
                        if rr is not None and re.search(r'\dX[\dH]', rr):
                            self.impliedBatterAdvance = 1  # he is safe!
                            self.isSafe = True
                        else:
                            self.isOut = True
                            self.isSafe = False
                    elif isTplPlay is True and numForced == 2:
                        # in theory should do the same search as in isDblPlay for two non-force out
                        # throws, but it doesn't change much and is insanely rare... TODO: do it!
                        self.isOut = True
                        self.isSafe = False

                    self.isDblPlay = isDblPlay
                    self.isTplPlay = isTplPlay

            return True
        return False

    def matchInterference(self, bb):
        # TODO: non-Catcher interference -- for stats; the baserunning results are the same.
        if bb.startswith('C') and not bb.startswith('CS'):  # interference, usually catcher
            self.isSafe = True  # catcher is charged with an error, runner is not charged with
            self.impliedBatterAdvance = 1  # an at bat. it is a plate appearance technically
            self.isAtBat = False           # but does NOT affect OBP (oh, boy...) TODO: This one
            self.isPlateAppearance = True
            self.ignoreForOBP = True
            return True
        return False

    def matchSingle(self, bb):
        if bb.startswith('S') and not bb.startswith('SB'):
            self.single = True
            self.totalBases = 1
            self.isSafe = True
            self.impliedBatterAdvance = 1
            return True
        return False

    def matchDouble(self, bb):
        if bb.startswith('D') and not bb.startswith('DI'):
            self.double = True
            self.totalBases = 2
            self.isSafe = True
            self.impliedBatterAdvance = 2
            if bb.startswith('DGR'):
                self.doubleGroundRule = True
            return True
        return False

    def matchTriple(self, bb):
        if bb.startswith('T'):
            self.triple = True
            self.totalBases = 3
            self.isSafe = True
            self.impliedBatterAdvance = 3
            return True
        return False

    def matchHomeRun(self, bb):
        if bb.startswith('H') and not bb.startswith('HP'):  # or HR
            self.homeRun = True
            self.totalBases = 4
            self.isSafe = True
            self.impliedBatterAdvance = 4
            return True
        return False

    def matchErrorOnFoul(self, bb):
        '''
        technically just on fly fouls
        '''
        if bb.startswith('FLE'):
            self.errors += 1  # \d will give whom to charge
            self.isSafe = False
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            return True
        return False

    def matchFielderError(self, bb):
        if bb.startswith('E'):
            self.errors += 1
            self.isSafe = True
            self.impliedBatterAdvance = 1
            return True
        return False

    def matchFieldersChoice(self, bb):
        if bb.startswith('FC'):
            # TODO: Harder -- but hopefully caught in the runner scores
            self.fieldersChoice = True
            self.impliedBatterAdvance = 1
            # figure out
            return True
        return False

    def matchHitByPitch(self, bb):
        if bb.startswith('HP'):
            self.hitByPitch = True
            self.isAtBat = False
            self.isSafe = True
            self.impliedBatterAdvance = 1
            return True
        return False

    def matchBalk(self, bb):
        if bb.startswith('BK'):
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.isBalk = True
            return True
        return False

    def matchDefensiveIndifference(self, bb):
        if bb.startswith('DI'):
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.defensiveIndifference = True
            return True
        return False

    def matchOtherAdvance(self, bb):
        # other advance (could be out (or not???))
        if bb.startswith('OA') or bb.startswith('OBA'):
            if bb.startswith('OBA'):
                print('Other Advance incorrectly encoded as OBA! at %r: %r. Fix!'
                      % (self,
                         self.parentByClass('Game')))
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.defensiveIndifference = False
            # self.isOut = True  # for not a player?
            return True

        return False

    def matchPassedBall(self, bb):
        if bb.startswith('PB'):  # needs explicit base runners
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.isPassedBall = True
            return True
        return False

    def matchWildPitch(self, bb):
        if bb.startswith('WP'):  # needs explicit base runners
            self.isNoPlay = True
            self.isAtBat = False  # what about strikeout wild pitch?
            self.isPlateAppearance = False
            self.isWildPitch = True
            return True
        return False

    def matchStolenBase(self, bb):
        # stolen bases are tricky because they may have implied base runners
        if bb.startswith('SB'):
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.stolenBase = True
            steals = bb.split(';')
            for s in steals:
                if self.basesStolen is None:
                    self.basesStolen = []
                self.basesStolen.append(s[2])
            return True
        return False

    def matchCaughtStealing(self, bb):
        if bb.startswith('CS'):
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.caughtStealing = True
            self.eraseBaseRunnerIfNoError('CS', bb)
            return True
        return False

    def matchPickoffCaughtStealing(self, bb):
        if bb.startswith('POCS'):  # before PO
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.isPickoff = True
            self.caughtStealing = True
            self.eraseBaseRunnerIfNoError('POCS', bb)
            return True
        return False

    def matchPickoff(self, bb):
        if bb.startswith('PO') and not bb.startswith('POCS'):
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.isPickoff = True
            self.eraseBaseRunnerIfNoError('PO', bb)
            return True
        return False


    parseMethodOrder = (matchStrikeout, matchBaseOnBalls, matchNoPlay,
                        matchGeneralOut, matchInterference,
                        matchSingle, matchDouble, matchTriple, matchHomeRun,
                        matchErrorOnFoul, matchFielderError, matchFieldersChoice,
                        # Things that move up a baserunner; all these should
                        # have explicit base runner information
                        matchHitByPitch, matchBalk, matchDefensiveIndifference,
                        matchOtherAdvance, matchWildPitch, matchPassedBall, matchStolenBase,
                        # things that eliminate a base runner
                        matchCaughtStealing, matchPickoffCaughtStealing, matchPickoff
                        # Sacrifice Fly, Sacrifice Hit
                        # SF / SH affects atBat status, but is in modifier. TODO: catch this.
                        )

    def splitBasicBatterModifiers(self, raw=''):
        '''
        Split on slashes not in parentheses and put the first group in
        self.basicBatter and all remaining groups into the self.modifiers list

        >>> from daseki import retro
        >>> pe = retro.play.PlayEvent()
        >>> pe.splitBasicBatterModifiers('S7/6-5(E/6)/Hi!')
        >>> pe.basicBatter
        'S7'
        >>> len(pe.modifiers)
        2
        >>> pe.modifiers[0]
        '6-5(E/6)'
        >>> pe.modifiers[1]
        'Hi!'
        '''
        if not raw:
            raw = self.raw
        # split on slashes not in parentheses
        bs = re.findall(r'(?:[^/(]|\([^)]*\))+', raw)
        # bs = raw.split('/')
        self.basicBatter = bs[0]

        if len(bs) > 1:
            self.modifiers = bs[1:]
        else:
            self.modifiers = []


    def eraseBaseRunnerIfNoError(self, playCode, fullPlay):
        '''
        given a playCode indicating an erased runner and the fullPlay,
        check to see if the fullPlay (including errors)
        means that we should still erase the runner.

        Also set the .basesStolen list

        Caught stealing base 3, erase base runner on second

        >>> from daseki import retro
        >>> pe = retro.play.PlayEvent()
        >>> pe.eraseBaseRunnerIfNoError('CS', 'CS3')
        >>> pe.eraseBaseRunners
        ['2']
        >>> print(pe.basesStolen)
        None

        Caught stealing base 3, but error!

        >>> pe = retro.play.PlayEvent()
        >>> pe.eraseBaseRunnerIfNoError('CS', 'CS3(E6)')
        >>> print(pe.eraseBaseRunners)
        None
        >>> pe.basesStolen
        ['3']



        Putout on first

        >>> pe = retro.play.PlayEvent()
        >>> pe.eraseBaseRunnerIfNoError('PO', 'PO1')
        >>> pe.eraseBaseRunners
        ['1']

        Attemped putout at first, but error:

        >>> pe = retro.play.PlayEvent()
        >>> pe.eraseBaseRunnerIfNoError('PO', 'PO1(E1)')
        >>> print(pe.eraseBaseRunners)
        None
        '''
        attemptedBaseSearch = re.search(playCode + r'([\dH])', fullPlay)
        if attemptedBaseSearch is None:
            raise RetrosheetException('PO or CS or POCS without a base!')
        attemptedBase = attemptedBaseSearch.group(1)
        safeOnError = ERROR_PAREN_RE.search(fullPlay)
        if DEBUG:
            print('checking for error: ', fullPlay, safeOnError)
        if safeOnError:
            if DEBUG:
                print('On play ' + playCode + ' =' + fullPlay
                      + '= safe on error, so credit a SB of '
                      + attemptedBase)
            if playCode != 'PO':  # pickoff does not advance a runner...
                self.stolenBase = False  # not for statistical purposes though...
                self.errors += 1
                if self.basesStolen is None:
                    self.basesStolen = []
                self.basesStolen.append(attemptedBase)
        else:
            subtractOne = {'H': '3', '3': '2', '2': '1'}
            if playCode != 'PO':
                eraseRunner = subtractOne[attemptedBase]
            else:
                eraseRunner = attemptedBase
            if self.eraseBaseRunners is not None:
                self.eraseBaseRunners.append(eraseRunner)
            else:
                self.eraseBaseRunners = [eraseRunner]


if __name__ == '__main__':
    import daseki
    daseki.mainTest()
