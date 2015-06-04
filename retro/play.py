import re
import weakref

HOME = 1
VISITOR = 0

DEBUG = False

ERROR_PAREN_RE = re.compile('\(\d*E\d*[\/A-Z]*\)')
ERROR_RE = re.compile('\d*E\d*[\/A-Z]*')

from bbbalk.exceptionsBB import RetrosheetException
from bbbalk.retro.datatypeBase import RetroData

class Play(RetroData):
    '''
    The most important and most complex record: records a play.
    '''
    record = 'play'
    visitorNames = ["visitor", "home"]
    def __init__(self, parent, inning, visitOrHome, playerId, count, pitches, playEvent):
        self.parent = weakref.ref(parent)
        self.inning = int(inning)
        self.visitOrHome = int(visitOrHome) # 0 = visitor, 1 = home
        self.visitName = self.visitorNames[int(visitOrHome)]
        self.playerId = playerId
        self.count = count
        self._pitches = pitches
        self.raw = playEvent
        self._playEvent = None
        self._runnerEvent = None
        
        self.runnersBefore = [None, None, None] # None, False, (True or a batterId)
        self.runnersAfter = [None, None, None] # None, False, (True or a batterId)
        
        rs = self.raw.split('.', 1)
        self._rawBatter = rs[0]
        if len(rs) > 1:
            self._rawRunners = rs[1]
        else:
            self._rawRunners = None

    @property
    def runnerEvent(self):
        if self._runnerEvent is not None:
            return self._runnerEvent
        self._runnerEvent = RunnerEvent(self, self._rawRunners, self.runnersBefore)
        return self._runnerEvent
        
    @property
    def playEvent(self):
        if self._playEvent is not None:
            return self._playEvent
        self._playEvent = PlayEvent(self, self._rawBatter)
        return self._playEvent


def _sortRunnerEvents(rEvt):
    '''
    helper function so that events beginning on 3rd sort first, then 2nd, then 1st, then B (batter)
    '''
    if rEvt == "2-1":
        # Just for Segura, Milwaukee 19 April 2013 -- Segura steals second then runs back to first
        # https://www.youtube.com/watch?v=HZM1JcJwo9E
        # sort last...
        return "X" + rEvt
    
    if rEvt[0] == "3":
        return "A" + rEvt
    elif rEvt[0] == "2":
        return "B" + rEvt
    elif rEvt[0] == "1":
        return "C" + rEvt
    elif rEvt[0] == 'B':
        return "D" + rEvt
    else:
        raise RetrosheetException("Unknown rEvt for sorting: %s" % rEvt)
        return "Z" + rEvt
    
    

class RunnerEvent(object):
    def __init__(self, parent, raw, runnersBefore):
        self.raw = raw
        self.parent = weakref.ref(parent)
        self.runnersBefore = runnersBefore
        self.runnersAfter = runnersBefore[:]
        if DEBUG:
            print(runnersBefore)
        

        if raw is not None:
            ra = raw.split(';')
        else:
            ra = []
        self._runnersAdvance = ra

        if parent.playEvent.stolenBase:
            for b in parent.playEvent.basesStolen:
                if b == '3' and not self.hasRunnerAdvance('2'):
                    ra.append('2-3')
                elif b == '2' and not self.hasRunnerAdvance('1'):
                    ra.append('1-2')
                elif b == 'H' and not self.hasRunnerAdvance('3'):
                    ra.append('3-H')
        
        for b in parent.playEvent.eraseBaseRunners:
            if b == '1' and not self.hasRunnerAdvance('1'):
                ra.append('1X2')
            elif b == '2' and not self.hasRunnerAdvance('2'):
                ra.append('2X3')
            elif b == '3' and not self.hasRunnerAdvance('3'):
                ra.append('3XH')


        self.outs = 0
        self.runs = 0
        self.scoringRunners = []
                
        if parent.playEvent.impliedBatterAdvance != 0:
            if not self.hasRunnerAdvance('B'):
                iba = parent.playEvent.impliedBatterAdvance
                bEvent = ""
                if iba == 1:
                    bEvent = 'B-1'
                elif iba == 2:
                    bEvent = 'B-2'
                elif iba == 3:
                    bEvent = 'B-3'
                elif iba == 4:
                    bEvent = 'B-H'
                else:
                    raise RetrosheetException("Huhhh??? Implied batter advance is strange")
                ra.append(bEvent)

        # in case of implied advances, we may get the same data twice.
        alreadyTakenCareOf = [False, False, False, False] # batter, first, second, third...
        
        # sort to make sure order still works...
        ra.sort(key=_sortRunnerEvents)
        
        for i in ra:
            isOut = False
            i = re.sub('\(\dX\)$', '', i)  # very few cases of 2X3(1X) such as COL200205190; redundant
            if '-' in i:
                before, after = i.split('-')
                #print("safe: %s %s" % (before, after))
            elif 'X' in i:
                try:
                    before, after = i.split('X')
                except ValueError:
                    print("Error in runnerAdvance: %s" % i)
                    print("Context: ", ra)
                    print("Inning", self.parent().inning)
                    print("Id", self.parent().parent().id)
                    raise
                isOut = True
                #print("out: %s %s" % (before, after))
            else:
                raise RetrosheetException("Something wrong with runner: %s: %s: %s" % (i, raw, parent.raw))
            beforeSmall = before[0]
            #beforeMods = before[1:]
            afterSmall = after[0]
            afterMods = after[1:]
            if ERROR_PAREN_RE.search(afterMods):
                # error, do not mark out...
                isOut = False
                # do something with errors
            
            batterInfo = True
            if beforeSmall == '1':
                if alreadyTakenCareOf[1]:
                    continue
                batterInfo = runnersBefore[0]
                alreadyTakenCareOf[1] = True
                self.runnersAfter[0] = False # assumes proper encoding order of advancement
            elif beforeSmall == '2':
                if alreadyTakenCareOf[2]:
                    continue
                batterInfo = runnersBefore[1]
                alreadyTakenCareOf[2] = True
                self.runnersAfter[1] = False # assumes proper encoding order of advancement
            elif beforeSmall == '3':
                if alreadyTakenCareOf[3]:
                    continue
                batterInfo = runnersBefore[2]
                alreadyTakenCareOf[3] = True
                self.runnersAfter[2] = False # assumes proper encoding order of advancement
            elif beforeSmall == 'B':
                if alreadyTakenCareOf[0]:
                    continue # implied batter but also given explicitly
                batterInfo = parent.playerId
                alreadyTakenCareOf[0] = True

            if isOut is False:
                if batterInfo is False:
                    print("\n****\nError about to occur!")
                    print("it is in Inning " + str(parent.inning))
                    print(ra)
                    print(runnersBefore)
                    print(self.runnersAfter)
                    print(self.parent().parent().id)
                    pass # debug
                if afterSmall == '1':
                    self.runnersAfter[0] = batterInfo
                    if DEBUG:
                        print(batterInfo + " goes to First")
                elif afterSmall == '2':
                    self.runnersAfter[1] = batterInfo
                    if DEBUG: 
                        print(batterInfo + " goes to Second")
                elif afterSmall == '3':
                    self.runnersAfter[2] = batterInfo
                    if DEBUG:
                        print(batterInfo + " goes to Third")
                elif afterSmall == 'H':
                    self.scoringRunners.append(batterInfo)
                    if DEBUG:
                        print(batterInfo + " scores!")
                    self.runs += 1
            else:
                if batterInfo is False:
                    print("\n****\nError about to occur!")
                    print("it is in Inning " + str(parent.inning) + ": " + str(parent.visitOrHome))
                    print(ra)
                    print(runnersBefore)
                    print(self.runnersAfter)
                    print(self.parent().parent().id)
                    pass # debug
                if DEBUG:
                    print(batterInfo + " is out")
                self.outs += 1
        parent.runnersAfter = self.runnersAfter
        
    def hasRunnerAdvance(self, letter):
        if isinstance(letter, int):
            letter = str(letter)
        for r in self._runnersAdvance:
            if r[0] == letter:
                return True
        return False

class PlayEvent(object):
    def __init__(self, parent, raw):
        self.raw = raw
        self.parent = weakref.ref(parent)      

        # split on slashes not in parentheses
        bs = re.findall(r'(?:[^\/(]|\([^)]*\))+', raw)
        #bs = raw.split('/')
        self.basicBatter = bs[0]
        if len(bs) > 1:
            self.modifiers = bs[1:]
        else:
            self.modifiers = []

        self.defaults()
        bb = self.basicBatter

        if bb.startswith('K'):
            self.strikeOut = True
            self.isOut = True
            afterEvent = re.match('K\d*\+(.*)', bb)
            if afterEvent:
                ## event after strike out...
                bb = afterEvent.group(1)
            ## K+event -- strike out but not out...
        elif bb.startswith('W') and not bb.startswith('WP'):
            self.baseOnBalls = True
            self.isSafe = True
            self.isAtBat = False
            self.impliedBatterAdvance = 1
            afterEvent = re.match('W\d*\+(.*)', bb)
            if afterEvent:
                ## event after walk... continue...
                bb = afterEvent.group(1)

        elif bb.startswith('IW') or bb.startswith('I'):
            # "I" is older style, seen a lot before 1997.
            self.baseOnBalls = True
            self.baseOnBallsIntentional = True
            self.isAtBat = False
            self.isSafe = True
            self.impliedBatterAdvance = 1
            afterEvent = re.match('IW?\d*\+(.*)', bb)
            if afterEvent:
                ## event after intentional walk... continue...
                bb = afterEvent.group(1)


        # Do not change to elif, because of plays after K, W, etc.
        if bb.startswith('NP'):
            self.isAtBat = False
            self.isPlateAppearance = False
            self.isNoPlay = True
        
        # most common...
        out = re.match('(\d+)', bb) 
        if out:
            safeOnError = ERROR_RE.search(bb)
            if safeOnError:
                self.isOut = False  # but out for statistics...
                self.impliedBatterAdvance = 1
            else:
                self.isOut = True
                self.fielders = list(out.group(1))
                numForced = 0
                for forces in re.finditer('\((\d)\)', bb):  # could be B also...
                    if DEBUG:
                        print(forces.group(1) + " FORCE OUT")
                    numForced += 1
                    self.eraseBaseRunners.append(forces.group(1))
                if numForced > 0:
                    isDblPlay = False
                    isTplPlay = False
                    for m in self.modifiers:
                        if 'GDP' in m or 'LDP' in m: # incl 'BGDP' for bunted                        
                            isDblPlay = True
                        if 'GTP' in m or 'LTP' in m: #
                            isTplPlay = True
                    if isDblPlay is False and isTplPlay is False:
                        self.impliedBatterAdvance = 1
                        self.isSafe = True # ?? 
                    elif isDblPlay is True and numForced == 2:
                        self.impliedBatterAdvance = 1  # he is safe!
                        self.isSafe = True # ?? 
            
        # TODO: keep track of outs on GDP, LDP, Triple plays
        
        # TODO: non-Catcher interference -- for stats, baserunning results are the same.
        if bb.startswith('C') and not bb.startswith('CS'): # interference, usually catcher
            self.isSafe = True  # catcher is charged with an error, runner is not charged with
            self.impliedBatterAdvance = 1  # an at bat. it is a plate appearance technically
            self.isAtBat = False           # but does NOT affect OBP (oh, boy...) TODO: This one
            self.isPlateAppearance = True
        
        
        ## single, double, triple, hr
        elif bb.startswith('S') and not bb.startswith('SB'):
            self.single = True
            self.totalBases = 1
            self.isSafe = True
            self.impliedBatterAdvance = 1
        elif bb.startswith('D') and not bb.startswith('DI'):
            self.double = True
            self.totalBases = 2
            self.isSafe = True
            self.impliedBatterAdvance = 2
            if bb.startswith('DGR'):
                self.doubleGroundRule = True
        elif bb.startswith('T'):
            self.triple = True
            self.totalBases = 3
            self.isSafe = True
            self.impliedBatterAdvance = 3
        elif bb.startswith('H') and not bb.startswith('HP'): # or HR
            self.homeRun = True
            self.totalBases = 4
            self.isSafe = True
            self.impliedBatterAdvance = 4
        
        # fielder errors
        elif bb.startswith('E'):
            self.error = True
            self.isSafe = True
            self.impliedBatterAdvance = 1
            
        elif bb.startswith('FC'): # TODO: Harder -- but hopefully caught in the runner scores
            self.fieldersChoice = True
            self.impliedBatterAdvance = 1
            ## figure out
            
        # error on foul fly ball
        elif bb.startswith('HP'):
            self.hitByPitch = True
            self.isAtBat = False
            self.isSafe = True
            self.impliedBatterAdvance = 1

        # SF / SH affects atBat status, but is in modifier. TODO: catch this.
        
        
        # No play...
        
        # Things that move up a baserunner; all these should have explicit base runner information
        elif bb.startswith('BK'):
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.isBalk = True
        elif bb.startswith('DI'):
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.defensiveIndifference = True
        elif bb.startswith('OA'):
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.defensiveIndifference = True
            self.isOut = True ## for not a player?
        elif bb.startswith('PB'):# needs explicit base runners
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.isPassedBall = True
        elif bb.startswith('WP'): # needs explicit base runners
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.isWildPitch = True
            
        ## stolen bases are tricky because they may have implied base runners
        elif bb.startswith('SB'):
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.stolenBase = True
            steals = bb.split(';')
            for s in steals:
                self.basesStolen.append(s[2])

        # things that eliminate a base runner
        elif bb.startswith('CS'):
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.isOut = True ## for not a player?
            self.caughtStealing = True
            self.eraseBaseRunnerIfNoError('CS', bb)
            
        elif bb.startswith('POCS'): # before PO
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.isPickoff = True
            self.isOut = True # decide...
            self.caughtStealing = True
            self.eraseBaseRunnerIfNoError('POCS', bb)
                                                    
        elif bb.startswith('PO') and not bb.startswith('POCS'):
            self.isNoPlay = True
            self.isAtBat = False
            self.isPlateAppearance = False
            self.isPickoff = True
            self.isOut = True # decide...
            self.eraseBaseRunnerIfNoError('PO', bb)
            
    def eraseBaseRunnerIfNoError(self, playCode, fullPlay):
        attemptedBaseSearch = re.search(playCode + '([\dH])', fullPlay)
        if attemptedBaseSearch is None:
            raise RetrosheetException('PO or CS or POCS without a base!')
        attemptedBase = attemptedBaseSearch.group(1)
        safeOnError = ERROR_PAREN_RE.search(fullPlay)
        if DEBUG:
            print("checking for error: ", fullPlay, safeOnError)
        if safeOnError:
            if DEBUG:
                print("On play " + playCode + " =" + fullPlay + "= safe on error, so credit a SB of " + attemptedBase)
            self.isOut = False  # but out for statistics..
            if playCode != 'PO': # pickoff does not advance a runner...
                self.stolenBase = True # not for statistical purposes though...
                self.basesStolen.append(attemptedBase)
        else:
            subtractOne = {'H': '3', '3': '2', '2': '1'}
            if playCode != 'PO':
                eraseRunner = subtractOne[attemptedBase]
            else:
                eraseRunner = attemptedBase
            self.eraseBaseRunners.append(eraseRunner)
            
        

    def defaults(self):
        self.isOut = False
        self.isSafe = False # in case of, say, a SB play, etc., both can be False
        self.fielders = []
        
        self.impliedBatterAdvance = 0
        
        self.single = False
        self.double = False
        self.doubleGroundRule = False
        self.triple = False
        self.homeRun = False

        self.strikeOut = False
        self.baseOnBalls = False
        self.baseOnBallsIntentional = False

        self.error = False
        self.fieldersChoice = False
        self.hitByPitch = False
        
        self.isAtBat = True
        self.isPlateAppearance = True
        self.isNoPlay = False
        
        self.isHit = False
        self.totalBases = 0

        self.stolenBase = False
        self.caughtStealing = False
        self.basesStolen = []
        self.eraseBaseRunners = []

        self.isPickoff = False
        self.isPassedBall = False
        self.isWildPitch = False
