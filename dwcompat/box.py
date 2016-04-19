#!/usr/bin/env python

from bbbalk.common import TeamNum
from bbbalk import game
import unittest

class BoxScore(object):
    def __init__(self, gameId):
        self.game = game.Game(gameId)
    
    def box(self):
        b = []
        b.append(self.topInfo())
        #b.append(self.mainBox())
        b.append(self.lineScore())
        #b.append(self.pitchers())
        b.append(self.bottom())
        return '\n'.join(b)
    
    def topInfo(self):
        g = self.game
        s = '     Game of '
        s += '{0.month}/{0.day}/{0.year}'.format(g.date)
        s += ' -- '
        s += g.visitingTeam.location
        s += ' at '
        s += g.homeTeam.location
        s += ' ('
        s += g.dayNight[0].upper()
        s += ')\n'
        return s
    
    def lineScore(self):
        g = self.game
        lines = {TeamNum.VISITOR: "", TeamNum.HOME: ""}
        maxInnings = g.numInnings
        
        for inning in range(1, maxInnings + 1):
            for teamNum in (TeamNum.VISITOR, TeamNum.HOME):
                hi = g.halfInningByNumber(inning, teamNum)
                if hi is None:
                    rStr = 'x'
                else:
                    r = hi.runs
                    rStr = str(r)
                    if r >= 10: # BOX does not justify
                        rStr = '(' + rStr + ')' 

                if inning % 3 == 0 and inning != maxInnings:
                    rStr += ' '
                lines[teamNum] += rStr
        
        b = ''        
        b += '{0:17s}{1} -- {2}\n'.format(g.visitingTeam.location, 
                                          lines[TeamNum.VISITOR], 
                                          g.runs.visitor)
        b += '{0:17s}{1} -- {2}\n'.format(g.homeTeam.location, 
                                          lines[TeamNum.HOME], 
                                          g.runs.home)
        return b
    
    def bottom(self):
        b = []
        #b.append(self.error())
        #b.append(self.dblplay())
        b.append(self.lob())
        dbl = self.dbl()
        if any(dbl):
            b.append(dbl)
        b.append(self.tpl())
        b.append(self.hr())
        #b.append(self.sb())
        #b.append(self.sh())
        #b.append(self.wildpitch())
        b.append(self.time())
        b.append(self.attendance())
        bs = '\n'.join(b)
        return bs
    
    def lob(self):
        g = self.game
        s = 'LOB -- '
        s += g.visitingTeam.location + " "
        s += str(g.leftOnBase.visitor)
        s += ', '
        s += g.homeTeam.location + " "
        s += str(g.leftOnBase.home)
        return s

    def countingStatHelper(self, attr, abbr):
        s = []
        game = self.game
        statDict = game.battersByEvent(attr)
        
        for pId in statDict:
            val = statDict[pId]
            if val == 1:
                vStr = ""
            else:
                vStr = " " + str(val)
            player = game.playerById(pId)
            pName = player.lastPlusInitial()
            s.append(pName + vStr)
        sStr = ', '.join(s)
        if len(s) > 0:
            return abbr + ' -- ' + sStr
        else:
            return ''
            
    def dbl(self):
        return self.countingStatHelper('double', '2B')

    def tpl(self):
        return self.countingStatHelper('triple', '3B')

    def hr(self):
        return self.countingStatHelper('homeRun', 'HR')


    def time(self):
        g = self.game
        t = g.infoByType('timeofgame')
        timeInfo = str(int(t/60)) + ':' + str(t % 60)
        s = 'T -- ' + timeInfo
        return s
    
    def attendance(self):
        g = self.game
        a = g.infoByType('attendance')
        return 'A -- ' + str(a)
    
    
    
class Test(unittest.TestCase):
    pass

    def testBox(self):
        auth = '''     Game of 3/30/2014 -- Los Angeles at San Diego (N)

  Los Angeles        AB  R  H RBI    San Diego          AB  R  H RBI
Crawford C, lf        4  0  1  1   Cabrera E, ss         2  1  0  0   
Puig Y, rf            3  0  0  0   Denorfia C, rf-lf     4  0  2  2   
Ramirez H, ss         4  0  0  0   Headley C, 3b         4  0  0  0   
Gonzalez A, 1b        4  0  0  0   Gyorko J, 2b          3  0  0  0   
Ethier A, cf          4  0  0  0   Alonso Y, 1b          4  0  0  0   
Uribe J, 3b           4  0  1  0   Medica T, lf          3  0  1  0   
Ellis A, c            3  0  2  0   Street H, p           0  0  0  0   
Gordon D, 2b          2  1  0  0   Venable W, cf-rf      3  0  1  0   
Ryu H, p              3  0  0  0   Rivera R, c           2  0  0  0   
Wilson B, p           0  0  0  0   Smith S, ph           1  1  1  1   
Perez C, p            0  0  0  0   Amarista A, cf        0  0  0  0   
Rodriguez P, p        0  0  0  0   Cashner A, p          1  0  0  0   
                                   Vincent N, p          0  0  0  0   
                                   Torres A, p           0  0  0  0   
                                   Thayer D, p           0  0  0  0   
                                   Grandal Y, ph-c       0  1  0  0   
                     -- -- -- --                        -- -- -- --
                     31  1  4  1                        27  3  5  3

Los Angeles      000 010 000 --  1
San Diego        000 000 03x --  3

  Los Angeles          IP  H  R ER BB SO
Ryu H                 7.0  3  0  0  3  7
Wilson B (L)*         0.0  2  3  2  1  0
Perez C               0.1  0  0  0  0  1
Rodriguez P           0.2  0  0  0  0  2

  San Diego            IP  H  R ER BB SO
Cashner A             6.0  4  1  1  2  5
Vincent N             0.2  0  0  0  1  1
Torres A              0.1  0  0  0  0  1
Thayer D (W)          1.0  0  0  0  0  1
Street H (S)          1.0  0  0  0  0  1
  * Pitched to 5 batters in 8th

E -- Wilson B, Gonzalez A
DP -- Los Angeles 2
LOB -- Los Angeles 6, San Diego 6
HR -- Smith S
SB -- Grandal Y
SH -- Cashner A, Cabrera E
WP -- Torres A
T -- 2:49
A -- 45567
'''
        bs = BoxScore('SDN201403300')
        print(bs.box())

    def testHighScoring(self):
        auth = '''     Game of 4/18/2009 -- Cleveland at New York (D)

  Cleveland          AB  R  H RBI    New York           AB  R  H RBI
Sizemore G, cf        4  3  3  1   Jeter D, ss           2  0  0  0   
Crowe T, cf           2  0  1  1   Ransom C, 3b          3  0  1  0   
DeRosa M, 3b          7  2  4  6   Damon J, dh           1  1  0  0   
Martinez V, c         4  2  2  2   Matsui H, ph          1  0  1  0   
Shoppach K, c         2  0  0  0   Teixeira M, 1b        3  1  1  2   
Hafner T, dh          7  3  3  1   Molina J, c           2  0  0  0   
Peralta J, ss         5  3  3  2   Swisher N, rf         3  0  0  0   
Choo S, rf            4  2  1  3   Posada J, c-1b        4  0  1  0   
Garko R, 1b           6  1  2  1   Cano R, 2b            4  1  1  0   
Francisco B, lf       5  3  2  0   Cabrera M, lf         3  1  1  2   
Cabrera A, 2b         6  3  4  5   Gardner B, cf         3  0  0  0   
                                   Pena R, 3b-ss         4  0  1  0   
                     -- -- -- --                        -- -- -- --
                     52 22 25 22                        33  4  7  4

Cleveland        0(14)1 140 011 -- 22
New York         200 002 000 --  4

  Cleveland            IP  H  R ER BB SO
Carmona F (W)         6.0  6  4  4  4  1
Kobayashi M           2.0  0  0  0  0  0
Chulk V               1.0  1  0  0  1  0

  New York             IP  H  R ER BB SO
Wang C (L)            1.1  8  8  8  0  1
Claggett A*           1.2  9  8  8  2  2
Ramirez E             2.0  3  4  4  3  4
Veras J               3.0  1  1  1  1  2
Marte D               1.0  4  1  1  0  1
  * Pitched to 2 batters in 4th

E -- Swisher N, Choo S
DP -- Cleveland 1
LOB -- Cleveland 9, New York 8
2B -- Francisco B 2, Sizemore G 2, DeRosa M, Hafner T, Peralta J, Matsui H
3B -- Ransom C        
HR -- Teixeira M, Choo S, Cabrera A, Sizemore G, DeRosa M, Martinez V, Cabrera M, Hafner T
HBP -- by Kobayashi M (Matsui H)
WP -- Wang C, Claggett A
T -- 3:49
A -- 45167
'''
        bs = BoxScore('NYA200904180')
        print(bs.box())


if __name__ == '__main__':
    import bbbalk
    bbbalk.mainTest(Test)