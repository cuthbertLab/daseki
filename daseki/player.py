# -*- coding: utf-8 -*-

from daseki.exceptionsDS import RetrosheetException
from daseki.retro.datatypeBase import RetroData
from daseki import common
from daseki.retro import play

_positionNames = "unknown pitcher catcher firstbase secondbase " + \
    "thirdbase shortstop leftfield centerfield rightfield " + \
    "designatedhitter pinchhitter pinchrunner"
positionNames = _positionNames.split()
positionAbbrevs = "unk p c 1b 2b 3b ss lf cf rf dh ph pr".split()
visitorNames = ["visitor", "home"]
del(_positionNames)


class PlayerYear(common.ParentType):
    '''
    Represents everything that a player does in a year, currently regular season only.
    '''
    __slots__ = ()
    #@common.keyword_only_args('parent')
    def __init__(self, playerId, parent=None):
        super(PlayerYear, self).__init__(parent=parent)
        

class PlayerGame(common.ParentType):
    '''
    Represents everything that a player does in one game.
    '''
    __slots__ = ('id', 'name', 'inning', 'visitOrHome', 'battingOrder',
                 'entryData', 'positions', 'subs', 'enteredFor', 'exitedFor',
                 'enteredPlay', 'exitedPlay', 'isStarter', 'isSub')
    #@common.keyword_only_args('parent')
    def __init__(self, playerId, playerName, visitOrHome, battingOrder, parent=None):
        super(PlayerGame, self).__init__(parent=parent)
        self.id = playerId
        self.name = playerName
        self.inning = None
        self.visitOrHome = int(visitOrHome) # 0 = visitor, 1 = home
        self.battingOrder = int(battingOrder)
        self.entryData = None
        self.positions = []
        self.subs = []
        self.enteredFor = None
        self.exitedFor = None
        self.enteredPlay = -1
        self.exitedPlay = 99999
        self.isStarter = False
        self.isSub = False

    def __repr__(self):
        return "<%s.%s %s,%s: %s (%s):%s>" % (self.__module__, self.__class__.__name__, 
                                  self.visitName, self.battingOrder, 
                                  self.name, self.id, self.positions)
    
    @property            
    def visitName(self):
        return visitorNames[self.visitOrHome]

    @property
    def hits(self):
        '''
        >>> g = game.Game('SDN201304090')
        >>> p = g.playerById('gyorj001')
        >>> p.hits
        1
        '''
        return self.countPlateAppearanceAttribute('isHit')

    @property
    def rbis(self):
        '''
        
        '''
        return self.countPlateAppearanceAttribute('rbis')

    @property
    def walks(self):
        '''
        No idea how Jed got into so much here
        
        >>> g = game.Game('SDN201304090')
        >>> p = g.playerById('gyorj001')
        >>> p.walks
        2
        '''
        return self.countPlateAppearanceAttribute('baseOnBalls')

    @property
    def atBats(self):
        '''
        
        '''
        return self.countPlateAppearanceAttribute('isAtBat')

    @property
    def strikeOuts(self):
        '''
        
        '''
        return self.countPlateAppearanceAttribute('strikeOut')

    @property
    def runs(self):
        '''
        >>> g = game.Game('SDN201304090')
        >>> p = g.playerById('venaw001')
        >>> p.runs
        2
        '''
        return len(self.plateAppearancesAsRunner(searchBefore=False, 
                                                 searchAfter=False, searchScoring=True))
    
    def plateAppearancesAsRunner(self, searchBefore=True, searchAfter=True, searchScoring=True):
        '''
        returns a list of all plate appearances where the player
        is a runner before or after the play, unless searchBefore is False
        or searchAfter is False.  If searchScoring is False then scoring runners
        will not count (do not turn all of them to False unless
        you love empty lists).
        
        Note that if a batter reaches base (even a home run) then the
        batter's own plate appearance will be included.
        
        Requires parent to be set to the game.
        
        Check against http://www.baseball-reference.com/boxes/SDN/SDN201304090.shtml
        
        >>> from pprint import pprint as pp

        >>> g = game.Game('SDN201304090')
        >>> p = g.playerById('venaw001')
        >>> pas = p.plateAppearancesAsRunner()
        >>> pp(pas)
        [<daseki.retro.play.PlateAppearance 1-2: venaw001: 
             [<daseki.retro.play.Play b1: venaw001:HR/9/L>]>,
         <daseki.retro.play.PlateAppearance 5-4: venaw001: 
             [<daseki.retro.play.Play b5: venaw001:CS2(26)>, 
              <daseki.retro.play.Play b5: venaw001:W>]>,
         <daseki.retro.play.PlateAppearance 5-5: quenc001: 
             [<daseki.retro.play.Play b5: quenc001:SB2>, 
              <daseki.retro.play.Play b5: quenc001:K>]>,
         <daseki.retro.play.PlateAppearance 7-5: venaw001: 
             [<daseki.retro.play.Play b7: venaw001:IW>]>,
         <daseki.retro.play.PlateAppearance 7-6: quenc001: 
             [<daseki.retro.play.Play b7: quenc001:HP.1-2>]>,
         <daseki.retro.play.PlateAppearance 7-7: alony001: 
             [<daseki.retro.play.Play b7: alony001:NP>, 
              <daseki.player.Sub visitor,5: Paco Rodriguez (rodrp001):pitcher>, 
              <daseki.retro.play.Play b7: alony001:NP>, 
              <daseki.player.Sub home,3: Tyson Ross (rosst001):pinchrunner>, 
              <daseki.retro.play.Play b7: alony001:9/F>]>,
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
             [<daseki.retro.play.Play b8: alony001:S6/G.3-H;1-2>]>]

        Only the times he was on base when the play began:
        
        >>> pas = p.plateAppearancesAsRunner(searchAfter=False, searchScoring=False)
        >>> pp(pas)
        [<daseki.retro.play.PlateAppearance 5-5: quenc001: 
             [<daseki.retro.play.Play b5: quenc001:SB2>, 
              <daseki.retro.play.Play b5: quenc001:K>]>,
         <daseki.retro.play.PlateAppearance 7-6: quenc001: 
             [<daseki.retro.play.Play b7: quenc001:HP.1-2>]>,
         <daseki.retro.play.PlateAppearance 7-7: alony001: 
             [<daseki.retro.play.Play b7: alony001:NP>, 
              <daseki.player.Sub visitor,5: Paco Rodriguez (rodrp001):pitcher>, 
              <daseki.retro.play.Play b7: alony001:NP>, 
              <daseki.player.Sub home,3: Tyson Ross (rosst001):pinchrunner>, 
              <daseki.retro.play.Play b7: alony001:9/F>]>,
         <daseki.retro.play.PlateAppearance 8-8(I): thayd001: 
             [<daseki.retro.play.Play b8: thayd001:NP>, 
              <daseki.player.Sub home,3: Jesus Guzman (guzmj005):pinchhitter>]>,
         <daseki.retro.play.PlateAppearance 8-8: guzmj005: 
             [<daseki.retro.play.Play b8: guzmj005:W>]>,
         <daseki.retro.play.PlateAppearance 8-9: alony001: 
             [<daseki.retro.play.Play b8: alony001:S6/G.3-H;1-2>]>]

        Only the plate appearances that had plays which ended with him still on base.  Note that
        a sub mid-PA will trigger a false entry:
        
        >>> pas = p.plateAppearancesAsRunner(searchBefore=False, searchScoring=False)
        >>> pp(pas)
        [<daseki.retro.play.PlateAppearance 5-4: venaw001: 
             [<daseki.retro.play.Play b5: venaw001:CS2(26)>, 
              <daseki.retro.play.Play b5: venaw001:W>]>,
         <daseki.retro.play.PlateAppearance 5-5: quenc001: 
             [<daseki.retro.play.Play b5: quenc001:SB2>, 
              <daseki.retro.play.Play b5: quenc001:K>]>,
         <daseki.retro.play.PlateAppearance 7-5: venaw001: 
             [<daseki.retro.play.Play b7: venaw001:IW>]>,
         <daseki.retro.play.PlateAppearance 7-6: quenc001: 
             [<daseki.retro.play.Play b7: quenc001:HP.1-2>]>,
         <daseki.retro.play.PlateAppearance 7-7: alony001: 
             [<daseki.retro.play.Play b7: alony001:NP>, 
              <daseki.player.Sub visitor,5: Paco Rodriguez (rodrp001):pitcher>, 
              <daseki.retro.play.Play b7: alony001:NP>, 
              <daseki.player.Sub home,3: Tyson Ross (rosst001):pinchrunner>, 
              <daseki.retro.play.Play b7: alony001:9/F>]>,
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
             [<daseki.retro.play.Play b8: guzmj005:W>]>]

        Only the times he scored or was thrown out.
        
        >>> pas = p.plateAppearancesAsRunner(searchBefore=False, searchAfter=False)
        >>> pp(pas)
        [<daseki.retro.play.PlateAppearance 1-2: venaw001: 
            [<daseki.retro.play.Play b1: venaw001:HR/9/L>]>,
         <daseki.retro.play.PlateAppearance 8-9: alony001: 
             [<daseki.retro.play.Play b8: alony001:S6/G.3-H;1-2>]>]
        '''
        pid = self.id
        game = self.parentByClass('Game')
        if game is None:
            return None
        visitOrHome = self.visitOrHome
        allPAs = []
        for hi in game.halfInnings:
            if hi.visitOrHome != visitOrHome:
                continue
            for pa in hi.plateAppearances:
                found = False
                for p in pa.events:                    
                    if p.record != 'play':
                        continue
                    if searchBefore is True:
                        for r in p.runnersBefore:
                            if r == pid:
                                found = True
                    if searchAfter is True:
                        for r in p.runnersAfter:
                            if r == pid:
                                found = True
                    if searchScoring is True:
                        for r in p.runnerEvent.scoringRunners:
                            if r == pid:
                                found = True
                if found is True:
                    allPAs.append(pa)
            
        return allPAs
        

    def lastPlusInitial(self):
        '''
        Return a string of the player's last name plus an initial
        
        TODO: Take from the ROS files to exact names..

        >>> g = game.Game('SDN201304090')
        >>> p = g.playerById('gyorj001')
        >>> p.lastPlusInitial()
        'Gyorko J'
        '''
        nameParts = self.name.split()
        firstInitial = nameParts[0][0]
        last = nameParts[-1]
        return last + " " + firstInitial
        

    def boxScoreStatline(self, fields='atBats runs hits walks strikeOuts', paddingInfo=None): 
        '''
        >>> g = game.Game('SDN201304090')
        >>> p = g.playerById('gyorj001')
        >>> print(p.boxScoreStatline('atBats hits runs strikeOuts'))
        Gyorko J 3b                      3   1   0   1

        >>> print(p.boxScoreStatline('atBats hits runs strikeOuts', 
        ...             paddingInfo={'nameSpace': 22, 'fieldSpace': 2}))
        Gyorko J 3b            3 1 0 1

        
        Compare:
        
        >>> g = game.Game('SFN200809260')
        >>> lc = g.lineupCards[common.TeamNum.VISITOR]
        >>> for pos in lc.playersByBattingOrder:
        ...    for p in pos:
        ...        print(p.boxScoreStatline('atBats runs hits rbis walks strikeOuts'))
        Furcal R ss                      2   0   0   0   1   0
          Berroa A pr,ss                 0   0   0   0   0   0
          Martin R ph,c                  1   1   1   2   0   0
        DeWitt B 3b                      5   1   1   0   0   1
        Ramirez M lf                     2   0   2   0   0   0
          McDonald J p                   0   0   0   0   0   0
          Ozuna P ph,2b                  3   0   0   0   0   0
        Kent J 2b                        3   1   1   2   0   0
          Young D lf,rf                  2   0   0   0   0   1
        Ethier A rf                      2   0   0   0   1   0
          Proctor S p                    0   0   0   0   0   0
          Park C p                       0   0   0   0   0   0
          Beimel J p                     0   0   0   0   0   0
          Sweeney M ph                   1   0   0   0   0   1
          Wade C p                       0   0   0   0   0   0
          Broxton J p                    0   0   0   0   0   0
          Stults E ph                    1   0   0   0   0   0
          Johnson J p                    0   0   0   0   0   0
        Loney J 1b                       4   1   1   1   0   1
        Pierre J cf,lf                   4   0   2   0   0   0
        Ardoin D c                       3   0   2   0   0   0
          Garciaparra N ph               1   0   1   0   0   0
          Ellis A pr                     0   1   0   0   0   0
          Hu C ss                        0   0   0   0   0   0
        Lowe D p                         1   0   0   0   0   0
          Repko J lf,rf                  2   0   0   0   0   2
          Kemp M ph,cf                   1   0   0   0   0   1
        '''
        if paddingInfo is None:
            pi = {}
        else:
            pi = paddingInfo.copy()

        if 'nameSpace' not in pi:
            pi['nameSpace'] = 30
        if 'subIndent' not in pi:
            pi['subIndent'] = 2
        if 'fieldSpace' not in pi:
            pi['fieldSpace'] = 4 

        
        if isinstance(fields, str):
            fields = fields.split()
        l = self.lastPlusInitial() + " " + ",".join([positionAbbrevs[p] for p in self.positions])
        if self.isSub:
            l = (" " * pi['subIndent']) + l
        l = l.ljust(pi['nameSpace'])
        for f in fields:
            l += str(getattr(self, f)).rjust(pi['fieldSpace'])
        return l

    def countPlateAppearanceAttribute(self, attr):
        '''
        Counts the number of times something occurs in all plate appearances in a game.
        
        >>> g = game.Game('SDN201304090')
        >>> p = g.playerById('gyorj001')
        >>> p.countPlateAppearanceAttribute('totalBases')
        1
        >>> p.countPlateAppearanceAttribute('rbis')
        1
        
        The number of errors made while he was at bat, not the number of errors he made.
        
        >>> p.countPlateAppearanceAttribute('errors')
        0

        Good game for Venable:

        >>> p = g.playerById('venaw001')
        >>> p.countPlateAppearanceAttribute('rbis')
        4
        '''
        total = 0
        for p in self.plateAppearances():
            v = getattr(p, attr)
            if v is True:
                total += 1
            elif isinstance(v, (float, int)):
                total += v
        return total

    def plateAppearances(self):
        '''
        Returns a list where each element represents a plateAppearance (even one that
        should not count for OBP such as Catcher's Interference) by the player and each 
        element in that list is itself a list of all Play objects representing that
        plate appearance.  The last play is the one that results in the end of the at bat.
        
        The first and last element in a PA are 'play' records.  Others may be subs or comments
        or something else.
        
        Requires parent to be set.
        
        >>> from pprint import pprint as pp
        
        >>> g = game.Game('SDN201304090')
        >>> p = g.playerById('gyorj001')
        >>> p
        <daseki.player.PlayerGame home,5: Jedd Gyorko (gyorj001):[5]>
        >>> pas = p.plateAppearances()
        >>> pp(pas)
        [<daseki.retro.play.PlateAppearance 1-5: gyorj001: 
            [<daseki.retro.play.Play b1: gyorj001:S8/G.2-H>]>,
         <daseki.retro.play.PlateAppearance 4-1: gyorj001: 
             [<daseki.retro.play.Play b4: gyorj001:9/F>]>,
         <daseki.retro.play.PlateAppearance 6-2: gyorj001: 
             [<daseki.retro.play.Play b6: gyorj001:K>]>,
         <daseki.retro.play.PlateAppearance 8-1: gyorj001: 
             [<daseki.retro.play.Play b8: gyorj001:NP>, 
              <daseki.player.Sub visitor,8: Jerry Hairston (hairj002):thirdbase>, 
              <daseki.retro.play.Play b8: gyorj001:NP>, 
              <daseki.player.Sub visitor,9: Nick Punto (puntn001):shortstop>, 
              <daseki.retro.play.Play b8: gyorj001:W>]>,
         <daseki.retro.play.PlateAppearance 8-10: gyorj001: 
             [<daseki.retro.play.Play b8: gyorj001:W.2-3;1-2>]>]
        >>> pas[0].isHit
        True
        >>> pas[0].baseOnBalls
        False
        '''
        pid = self.id
        game = self.parentByClass('Game')
        if game is None:
            return None
        visitOrHome = self.visitOrHome
        allPAs = []
        for hi in game.halfInnings:
            if hi.visitOrHome != visitOrHome:
                continue
            for pa in hi.plateAppearances:
                if pa.batterId == pid:
                    allPAs.append(pa)
            
        return allPAs
        

class LineupCard(common.ParentType):
    '''
    Represents all of the players for a given team for a given game.

    >>> from pprint import pprint as pp
    
    >>> g = game.Game('SDN201304090')
    >>> lc = g.lineupCards[common.TeamNum.VISITOR]
    >>> lc
    <daseki.player.LineupCard visitor (SDN201304090)>
    >>> pp(lc.playersByBattingOrder)
    [[],
     [<daseki.player.PlayerGame visitor,1: Carl Crawford (crawc002):[7]>],
     [<daseki.player.PlayerGame visitor,2: Mark Ellis (ellim001):[4]>],
     [<daseki.player.PlayerGame visitor,3: Matt Kemp (kempm001):[8]>],
     [<daseki.player.PlayerGame visitor,4: Adrian Gonzalez (gonza003):[3]>],
     [<daseki.player.PlayerGame visitor,5: Juan Uribe (uribj002):[5]>,
      <daseki.player.PlayerGame visitor,5: Ronald Belisario (belir001):[1]>,
      <daseki.player.PlayerGame visitor,5: Paco Rodriguez (rodrp001):[1]>,
      <daseki.player.PlayerGame visitor,5: Matt Guerrier (guerm001):[1]>,
      <daseki.player.PlayerGame visitor,5: Luis Cruz (cruzl001):[5]>],
     [<daseki.player.PlayerGame visitor,6: Andre Ethier (ethia001):[9]>],
     [<daseki.player.PlayerGame visitor,7: A.J. Ellis (ellia001):[2]>],
     [<daseki.player.PlayerGame visitor,8: Justin Sellers (sellj002):[6]>,
      <daseki.player.PlayerGame visitor,8: Jerry Hairston (hairj002):[11, 5]>,
      <daseki.player.PlayerGame visitor,8: J.P. Howell (howej003):[1]>],
     [<daseki.player.PlayerGame visitor,9: Josh Beckett (beckj002):[1]>,
      <daseki.player.PlayerGame visitor,9: Skip Schumaker (schus001):[11]>,
      <daseki.player.PlayerGame visitor,9: Chris Capuano (capuc001):[1]>,
      <daseki.player.PlayerGame visitor,9: Nick Punto (puntn001):[5, 6]>]]
    '''
    
    __slots__ = ('lineupData', 'playersByBattingOrder', 
                 'visitOrHome', 'teamAbbreviation', 'allPlayers')
    #@common.keyword_only_args('parent')
    def __init__(self, visitOrHome, parent=None):
        super(LineupCard, self).__init__(parent=parent)
        self.lineupData = []
        self.playersByBattingOrder = [[] for _ in range(10)] # 0 will always be None
        self.visitOrHome = visitOrHome
        self.teamAbbreviation = None
        self.allPlayers = []

    def __repr__(self):
        gi = ""
        p = self.parentByClass('Game') 
        if p is not None:
            gi = p.id
        return "<%s.%s %s (%s)>" % (self.__module__, self.__class__.__name__, 
                                  visitorNames[self.visitOrHome], gi)

    def playerById(self, playerId):
        '''
        Returns the PlayerGame object representing a playerId in this game:
        
        >>> g = game.Game('SDN201304090')
        >>> lc = g.lineupCards[common.TeamNum.HOME]
        >>> lc.playerById('gyorj001')
        <daseki.player.PlayerGame home,5: Jedd Gyorko (gyorj001):[5]>
        '''
        for p in self.allPlayers:
            if p.id == playerId:
                return p
        return None


    def add(self, playerEntrance):
        '''
        Adds a PlayerEntrance object to the lineup card
        '''
        self.lineupData.append(playerEntrance)
        pbbo = self.playersByBattingOrder[playerEntrance.battingOrder]
        found = None
        for p in pbbo:
            if p.id == playerEntrance.id:
                found = p
        if found is None:
            player = PlayerGame(playerEntrance.id, playerEntrance.name, 
                                playerEntrance.visitOrHome, playerEntrance.battingOrder,
                                parent=self)
            if playerEntrance.record == 'start':
                player.isStarter = True
            else:
                player.isSub = True
                player.enteredPlay = playerEntrance.playNumber
            player.entryData = playerEntrance
            pbbo.append(player)
            self.allPlayers.append(player)
        else:
            player = found
            player.subs.append(playerEntrance)
        player.positions.append(playerEntrance.position)
            

    
    def byPlayNumber(self, num):
        '''
        Return the substitution at a given play number.  The only one that should have
        multiple is playNumber -1
        
        >>> g = game.Game('SDN201304090')
        >>> lc = g.lineupCards[common.TeamNum.HOME]
        >>> lc.byPlayNumber(42)
        <daseki.player.Sub home,9: Eric Stults (stule002):pinchhitter>        
        '''
        for d in self.lineupData:
            if d.playNumber == num:
                return d
        return None
        
    def playsWithSubstitutions(self, startNumber=0, endNumber=99999):
        '''
        Return a list of all plays where someone substituted.

        >>> g = game.Game('SDN201304090')
        >>> lc = g.lineupCards[common.TeamNum.HOME]
        >>> lc.playsWithSubstitutions()
        [42, 49, 61, 63, 69, 75, 77, 78, 96, 101]

        Limit to a range:
        
        >>> lc.playsWithSubstitutions(61, 78)
        [61, 63, 69, 75, 77, 78]


        >>> lc2 = g.lineupCards[common.TeamNum.VISITOR]
        >>> lc2.playsWithSubstitutions()
        [52, 54, 65, 66, 74, 81, 83, 84, 88, 93, 94]
        '''
        return [r.playNumber for r in self.lineupData if r.playNumber >= startNumber and 
                    r.playNumber <= endNumber]

    def subsFor(self, player):
        '''
        return the player card of the player that this player substituted for.
        
        It may be the same player if the position changes, as in the example below:
        
        >>> g = game.Game('SDN201304090')
        >>> lc = g.lineupCards[common.TeamNum.VISITOR]
        >>> p = g.subByNumber(83)
        >>> p
        <daseki.player.Sub visitor,8: Jerry Hairston (hairj002):thirdbase>
        >>> lc.subsFor(p)
        <daseki.player.Sub visitor,8: Jerry Hairston (hairj002):pinchhitter>
        
        If parent is set, we can also just do:
        
        >>> lc.subsFor(83)
        <daseki.player.Sub visitor,8: Jerry Hairston (hairj002):pinchhitter>


        Chain it: Who did J.P. Howell sub for, and who did that person sub for, etc.
        
        >>> pn = 94
        >>> print(lc.byPlayNumber(pn))
        <daseki.player.Sub visitor,8: J.P. Howell (howej003):pitcher>
        >>> while True:
        ...    p = lc.subsFor(pn)
        ...    if p is None:
        ...        break
        ...    pn = p.playNumber
        ...    print(pn, "i:", p.inning, p)
        83 i: 8 <daseki.player.Sub visitor,8: Jerry Hairston (hairj002):thirdbase>
        81 i: 8 <daseki.player.Sub visitor,8: Jerry Hairston (hairj002):pinchhitter>
        -1 i: 0 <daseki.player.Start visitor,8: Justin Sellers (sellj002):shortstop>
        '''
        if hasattr(player, 'record') is True:
            playNum = player.playNumber
        else:
            playNum = player
            player = self.byPlayNumber(playNum)
        
        battingPosition = player.battingOrder
        playNumSearch = playNum - 1
        while playNumSearch >= -1:
            battingOrderBefore = self.battingOrderAtPlayNumber(playNumSearch)
            thisPlayer = battingOrderBefore[battingPosition]
            if thisPlayer is player:
                playNumSearch -= 1
            else:
                return thisPlayer
        return None # shouldn't happen unless -1 is given to begin with
        
        

    def multipleSubs(self, startNumber=0, endNumber=99999):
        '''
        find all times where multiple substitutions happened in the same play sequence.
        
        Requires parent to be set.

        >>> g = game.Game('SDN201304090')
        >>> lc = g.lineupCards[common.TeamNum.HOME]
        >>> ms = lc.multipleSubs()
        >>> ms
        [[<daseki.player.Sub home,3: Dale Thayer (thayd001):pitcher>, 
          <daseki.player.Sub home,9: Chris Denorfia (denoc001):leftfield>]]
        >>> ms[0][0].playNumber
        77
        
        >>> lc2 = g.lineupCards[common.TeamNum.VISITOR]
        >>> lc2.multipleSubs()
        [[<daseki.player.Sub visitor,5: Ronald Belisario (belir001):pitcher>, 
          <daseki.player.Sub visitor,9: Nick Punto (puntn001):thirdbase>], 
         [<daseki.player.Sub visitor,8: Jerry Hairston (hairj002):thirdbase>, 
          <daseki.player.Sub visitor,9: Nick Punto (puntn001):shortstop>], 
         [<daseki.player.Sub visitor,5: Luis Cruz (cruzl001):thirdbase>, 
          <daseki.player.Sub visitor,8: J.P. Howell (howej003):pitcher>]]
        '''
        ps = self.playsWithSubstitutions(startNumber, endNumber)
        ms = []
        checkedSubs = []
        for playNumber in ps:
            if playNumber in checkedSubs:
                continue
            thisSub = [self.parent.subByNumber(playNumber)]
            keepSearching = True
            searchNumber = playNumber + 1
            while keepSearching:
                p = self.parent.playByNumber(searchNumber)
                if p is None or p.playEvent.isNoPlay is False:
                    # there may be shifts on both sides...so cannot just do +1
                    keepSearching = False  
                if searchNumber in ps: # could be a switch on the other team
                    thisSub.append(self.parent.subByNumber(searchNumber))
                    checkedSubs.append(searchNumber)
                searchNumber += 1
            if len(thisSub) > 1:
                ms.append(thisSub)
        return ms

    def battingOrderAtPlayNumber(self, playNumber=0):
        '''
        looks through the lineup card and sees who is at each point 
        in the lineup at a given play number

        1 indexed. so 0 is always None in non DH games, and pitcher in DH games

        >>> from pprint import pprint as pp
        >>> g = game.Game('SDN201304090')
        >>> lc = g.lineupCards[common.TeamNum.HOME]
        >>> pp(lc.battingOrderAtPlayNumber(0)) # default
        [None,
         <daseki.player.Start home,1: Everth Cabrera (cabre001):shortstop>,
         <daseki.player.Start home,2: Will Venable (venaw001):rightfield>,
         <daseki.player.Start home,3: Carlos Quentin (quenc001):leftfield>,
         <daseki.player.Start home,4: Yonder Alonso (alony001):firstbase>,
         <daseki.player.Start home,5: Jedd Gyorko (gyorj001):thirdbase>,
         <daseki.player.Start home,6: Alexi Amarista (amara001):secondbase>,
         <daseki.player.Start home,7: Cameron Maybin (maybc001):centerfield>,
         <daseki.player.Start home,8: Nick Hundley (hundn001):catcher>,
         <daseki.player.Start home,9: Clayton Richard (richc002):pitcher>] 

        >>> pp(lc.battingOrderAtPlayNumber(999))
        [None,
         <daseki.player.Start home,1: Everth Cabrera (cabre001):shortstop>,
         <daseki.player.Start home,2: Will Venable (venaw001):rightfield>,
         <daseki.player.Sub home,3: Brad Brach (bracb001):pitcher>,
         <daseki.player.Start home,4: Yonder Alonso (alony001):firstbase>,
         <daseki.player.Start home,5: Jedd Gyorko (gyorj001):thirdbase>,
         <daseki.player.Start home,6: Alexi Amarista (amara001):secondbase>,
         <daseki.player.Start home,7: Cameron Maybin (maybc001):centerfield>,
         <daseki.player.Start home,8: Nick Hundley (hundn001):catcher>,
         <daseki.player.Sub home,9: Chris Denorfia (denoc001):leftfield>] 
        '''
        # store as batting position, so 0 will always be None for NL
        batters = [None for i in range(10)] 
        for p in self.lineupData:
            if p.playNumber > playNumber:
                break
            batters[p.battingOrder] = p
        return batters


class PlayerEntrance(RetroData):
    '''
    a player's appearance in a game or his new position after a defensive switch.  
    
    It has information such as:
    
    .id -- playerId
    .name -- name
    .visitOrHome -- 0 = visitor, 1 = home
    .visitName -- "visitor" or "home"
    .battingOrder -- 0-9 (0 = pitcher in DH)
    .position -- 1-9, 10 for DH, 11 for pinch hitter, 12 for pinch runner, 0 = unknown
    .positionName
    '''    
    
    __slots__ = ('id', 'name',  'visitOrHome', 'battingOrder', 'position', 'inning')
    
    def __init__(self, playerId, playerName, visitOrHome, battingOrder, position, parent=None):
        super(PlayerEntrance, self).__init__(parent=parent)
        try:
            self.id = playerId
            self.name = playerName
            self.visitOrHome = int(visitOrHome) # 0 = visitor, 1 = home
            self.battingOrder = int(battingOrder)
            self.inning = None
#             if position.endswith('"'): 
#                 # parse error in 1996KCA.EVA and 1996MON.EVN # TODO: Tell Retrosheet
#                 gid = self.parentByClass('Game').id
#                 common.warn("Position ending in quote in {0}".format(gid))
#                 position = position[0:len(position)-1]
            self.position = int(position)
        except ValueError as ve:
            raise RetrosheetException("Parse error for player {0}: {1}".format(playerName, str(ve)))

    def __repr__(self):
        return "<%s.%s %s,%s: %s (%s):%s>" % (self.__module__, self.__class__.__name__, 
                                  self.visitName, self.battingOrder, 
                                  self.name, self.id, self.positionName)

    @property            
    def positionName(self):
        return positionNames[self.position]

    @property            
    def visitName(self):
        return visitorNames[self.visitOrHome]



class Start(PlayerEntrance):
    record = 'start'
    __slots__ = ()
    def __init__(self, playerId, playerName, visitOrHome, battingOrder, position, parent=None):
        super(Start, self).__init__(playerId, playerName, visitOrHome, 
                                    battingOrder, position, parent=parent)

class Sub(PlayerEntrance):
    record = 'sub'
    __slots__ = ()
    def __init__(self, playerId, playerName, visitOrHome, battingOrder, position, parent=None):
        super(Sub, self).__init__(playerId, playerName, visitOrHome, 
                                  battingOrder, position, parent=parent)

if __name__ == "__main__":
    import daseki
    daseki.mainTest()
    
