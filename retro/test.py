HOME = 1
VISITOR = 0


from bbbalk import common
from bbbalk.retro.parser import EventFile, YearDirectory # @UnresolvedImport
from bbbalk.games import Game # @UnresolvedImport

class Test():
    def sdAttendance(self):
        yd = YearDirectory(2014)
        attd = 0
        for pg in yd.byTeam('SDN'):
            g = Game()
            g.mergeProto(pg)
            att = g.infoByType('attendance')
            print(g.id, att)
            attd += int(att)
        print("******", attd)

    def yearsList(self):
        for thisYear in range(1995, 2015):
            print("Parsing: ", thisYear)
            yd = YearDirectory(thisYear)
            yd.parseEventFiles()
            
    def yearList(self, year=2014):
        yd = YearDirectory(year)
        yd.parseEventFiles()
    
    def pitcherBats(self):
        '''
        how often did the pitcher bat in the first inning?
        
        1995-2014:
        games 25140 
        happened 11552 
        420 times in the first inning
        percentage 45% 

        2010-2015
        43% of time.
        '''
        gamesPitched = {}
        
        for thisYear in range(2010, 2015):
            yd = YearDirectory(thisYear)
            yd.parseEventFiles()
            
            for ev in yd.eventFiles:
                for pg in ev.protoGames:
                    g = pg.parse()
                    visitorTeam = g.visitingTeam
                    if visitorTeam not in gamesPitched:
                        gamesPitched[visitorTeam] = [0, 0, 0]
                    if not g.hasDH():
                        gamesPitched[visitorTeam][0] += 1
                        starters = g.starters(VISITOR)
                        startingPitcher = starters[-1] # TODO: get by position
                        #print(startingPitcher.name)
                        for r in g.recordsByType('play'):
                            if r.inning <= 2 and r.visitOrHome == VISITOR and r.playerId == startingPitcher.id:
                                #print("********Yup")
                                gamesPitched[visitorTeam][r.inning] += 1

        totTot = 0
        totTotUsed = 0
        totTot1st = 0
        
        for tn in sorted(gamesPitched):
            totalGames = gamesPitched[tn][0]
            i1 = gamesPitched[tn][1] 
            i2 = gamesPitched[tn][2] 
            totalPitcherUsed = i1 + i2
            percentage = int(100 * totalPitcherUsed/(totalGames+0.00001))
            totTot += totalGames
            totTotUsed += totalPitcherUsed
            totTot1st += i1
            if (totalGames > 10):
                print(tn, totalGames, totalPitcherUsed, percentage, i1, i2)
        
        percentage = int(100 * totTotUsed/totTot)
        print("***", totTot, totTotUsed, percentage, totTot1st)
    
    def events(self):
        ev = EventFile(common.dataDirByYear(2014) + '/2014SDN.EVN')
        g = Game()
        g.mergeProto(ev.protoGames[0])
        for p in g.recordsByType('play'):
            e = p.playEvent
            print(p.inning, p.visitOrHome, p.playerId, e.basicBatter, e.isOut, e.isSafe, e.raw)
            p.runnerEvent

    def checkScores(self):
        global DEBUG
        DEBUG = True
        ev = EventFile(common.dataDirByYear(2014) + '/2014SDN.EVN')
        for pg in ev.protoGames:
            g = Game()
            g.mergeProto(pg)
            print(g.id, g.runs)        
            
    
if __name__ == '__main__':
    t = Test()
    #t.checkScores()
    #t.events()
    #t.pitcherBats()
    #t.yearList(1999)
    #t.yearsList()
    t.sdAttendance()