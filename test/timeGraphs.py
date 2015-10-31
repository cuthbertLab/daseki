import pycallgraph # @UnusedImport
import pycallgraph.output
import time
import sys

# this class is duplicated from common.py in order to avoid 
# import the module for clean testing
class Timer(object):
    """An object for timing."""
        
    def __init__(self):
        # start on init
        self._tStart = time.time()
        self._tDif = 0
        self._tStop = None

    def start(self):
        '''Explicit start method; will clear previous values. 
        Start always happens on initialization.'''
        self._tStart = time.time()
        self._tStop = None # show that a new run has started so __call__ works
        self._tDif = 0
    
    def stop(self):
        self._tStop = time.time()
        self._tDif = self._tStop - self._tStart

    def clear(self):
        self._tStop = None
        self._tDif = 0
        self._tStart = None

    def __call__(self):
        '''Reports current time or, if stopped, stopped time.
        '''
        # if stopped, gets _tDif; if not stopped, gets current time
        if self._tStop == None: # if not stoped yet
            t = time.time() - self._tStart
        else:
            t = self._tDif
        return t 

    def __str__(self):
        if self._tStop == None: # if not stoped yet
            t = time.time() - self._tStart
        else:
            t = self._tDif
        return str(round(t,3))

#-------------------------------------------------------------------------------
class CallTest(object):
    '''Base class for timed tests
    '''
    def __init__(self):
        '''Perform setup routines for tests
        '''
        pass 

    def testFocus(self):
        '''Calls to be timed
        '''
        pass # run tests


class BBBCallTest(CallTest):
    '''Base class for timed tests that need bbbalk importerd
    '''
    def __init__(self):
        '''Perform setup routines for tests
        '''
        import bbbalk
        self.bbb = bbbalk

class ParseOneSeason(BBBCallTest):
    def testFocus(self):
        bbbalk = self.bbb
        gc = bbbalk.games.GameCollection()
        gc.yearStart = 2013
        gc.yearEnd = 2013
        gc.team = 'SDN'
        games = gc.parse()

class ProtoParse(BBBCallTest):
    def testFocus(self):
        bbbalk = self.bbb
        parser = bbbalk.retro.parser
        yd = parser.YearDirectory(2013)
        pgs = yd.byPark('SDN')
        


class CallGraph(object):
    def __init__(self):
        self.includeList = None
        self.excludeList = ['pycallgraph.*']
        self.excludeList += ['re.*','sre_*']
        # these have been shown to be very fast
        #self.excludeList += ['*meter*', 'encodings*', '*isClass*', '*duration.Duration*']

        # set class  to test here
        #self.callTest = ParseOneSeason
        self.callTest = ProtoParse
        # common to all call tests. 
        if hasattr(self.callTest, 'includeList'):
            self.includeList = self.callTest.includeList

    def run(self, runWithEnviron=True):
        '''
        Main code runner for testing. To set a new test, 
        update the self.callTest attribute in __init__(). 
        
        Note that the default of runWithEnviron imports music21.environment.  That might
        skew results
        '''
        suffix = '.png' # '.svg'
        outputFormat = suffix[1:]
        _MOD = "test.timeGraphs.py"

        if runWithEnviron:
            from music21 import environment
            environLocal = environment.Environment(_MOD)
            fp = environLocal.getTempFile(suffix)
        # manually get a temporary file
        else:
            import tempfile
            import os
            if os.name in ['nt'] or sys.platform.startswith('win'):
                platform = 'win'
            else:
                platform = 'other'
            
            tempdir = os.path.join(tempfile.gettempdir(), 'music21')
            if platform != 'win':
                fd, fp = tempfile.mkstemp(dir=tempdir, suffix=suffix)
                if isinstance(fd, int):
                # on MacOS, fd returns an int, like 3, when this is called
                # in some context (specifically, programmatically in a 
                # TestExternal class. the fp is still valid and works
                # TODO: this did not work on MacOS 10.6.8 w/ py 2.7
                    pass
                else:
                    fd.close() 
            else:
                tf = tempfile.NamedTemporaryFile(dir=tempdir, suffix=suffix)
                fp = tf.name
                tf.close()

 
        if self.includeList is not None:
            gf = pycallgraph.GlobbingFilter(include=self.includeList, exclude=self.excludeList)
        else:
            gf = pycallgraph.GlobbingFilter(exclude=self.excludeList)
        # create instance; will call setup routines
        ct = self.callTest()

        # start timer
        print('%s starting test' % _MOD)
        t = Timer()
        t.start()

        graphviz = pycallgraph.output.GraphvizOutput(output_file=fp)
        graphviz.tool = '/usr/local/bin/dot'
        
        config = pycallgraph.Config()
        config.trace_filter = gf

        with pycallgraph.PyCallGraph(output=graphviz, config=config):
            ct.testFocus() # run routine

        print('elapsed time: %s' % t)
        # open the completed file
        print('file path: ' + fp)
        try:
            environLocal = environment.Environment(_MOD)
            environLocal.launch(outputFormat, fp)
        except NameError:
            pass


if __name__ == '__main__':
    sys.path.append('/Users/Cuthbert/git/music21base')
    cg = CallGraph()
    cg.run()
