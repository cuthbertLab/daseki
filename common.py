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

try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

try:
    import enum
except ImportError:
    from bbbalk.ext import enum

import functools
import inspect
import re
import os
import sys
import time
import tempfile
import weakref

from bbbalk.ext import six
from bbbalk.exceptionsBB import BBBalkException

class TeamNum(enum.IntEnum):
    VISITOR = 0
    HOME = 1


# tools for setup.py
def sourceFilePath():
    '''
    Get the BBBalk directory that contains source files. This is not the same as the
    outermost package development directory.
    '''
    import bbbalk # pylint: disable=redefined-outer-name
    fpBalk = bbbalk.__path__[0] # list, get first item 
    # use corpus as a test case
    if 'retro' not in os.listdir(fpBalk):
        raise Exception('cannot find expected bbbalk directory: %s' % fpBalk)
    return fpBalk

def dataFilePath():
    return os.path.join(sourceFilePath(), 'dataFiles')

def dataRetrosheet():
    return os.path.join(dataFilePath(), 'retrosheet')

def dataRetrosheetEvent():
    return os.path.join(dataRetrosheet(), 'event')

def dataRetrosheetByType(gameType='regular'):
    if gameType not in ('asg', 'post', 'regular'):
        raise BBBalkException("gameType must be asg, post, or regular, not {0}".format(gameType))
    return os.path.join(dataRetrosheetEvent(), gameType)

def gameLogFilePath():
    return os.path.join(dataRetrosheet(), 'gamelog')

#----------------------
def getDefaultRootTempDir(self):
    '''
    returns whatever tempfile.gettempdir() returns plus 'bbbalk'.
    
    Creates the subdirectory if it doesn't exist:
    
    >>> import tempfile
    >>> t = tempfile.gettempdir()
    >>> #_DOCS_SHOW t
    '/var/folders/x5/rymq2tx16lqbpytwb1n_cc4c0000gn/T'

    >>> import os
    >>> common.getDefaultRootTempDir() == os.path.join(t, 'bbbalk')
    True
    '''
    # this returns the root temp dir; this does not create a new dir
    dstDir = os.path.join(tempfile.gettempdir(), 'bbbalk')
    # if this path already exists, we have nothing more to do
    if os.path.exists(dstDir):
        return dstDir
    else:
        # make this directory as a temp directory
        try:
            os.mkdir(dstDir)
        except OSError:  # cannot make the directory
            dstDir = tempfile.gettempdir()
        return dstDir


#---------------------
GAMEID_MATCH = re.compile('([A-Za-z][A-Za-z][A-Za-z])(\d\d\d\d)(\d\d)(\d\d)(\d?)')

class GameId(object):
    '''
    >>> gid = common.GameId('SDN201304090')
    >>> str(gid)
    'SDN201304090'
    >>> gid
    <bbbalk.common.GameId SDN201304090>
    >>> gid.year
    2013
    >>> gid.day
    9
    >>> gid.gameNum # always a string because of weird split dblheader A, B codes
    '0'
    >>> gid.homeTeam
    'SDN'
    
    >>> gid2 = common.GameId()
    >>> gid2.homeTeam = 'ARI'
    >>> gid2.year = 2000
    >>> gid2.month = 9
    >>> gid2.day = 22
    >>> print(gid2)
    ARI200009220
    '''
    
    def __init__(self, gameId=None):
        self.gameId = gameId
        self.year = 0
        self.month = 0
        self.day = 0
        self.gameNum = "0"
        self.homeTeam = "XXX"
        if gameId is not None:
            self.parse()
    
    def __repr__(self):
        return "<{0}.{1} {2}>".format(self.__module__, self.__class__.__name__, str(self))
    
    def __str__(self):
        return "{s.homeTeam}{s.year:4d}{s.month:02d}{s.day:02d}{s.gameNum}".format(s=self)
    
    
    def parse(self):
        gameId = self.gameId
        matched = GAMEID_MATCH.match(gameId)
        if not matched:
            raise BBBalkException('invalid gameId: %s' % gameId)
        self.homeTeam = matched.group(1).upper()
        self.year = int(matched.group(2))
        self.month = int(matched.group(3))
        self.day = int(matched.group(4))
        self.gameNum = matched.group(5)
        if self.gameNum == '':
            self.gameNum = "0"



#---------------------

ordinals = ["Zeroth","First","Second","Third","Fourth","Fifth",
            "Sixth","Seventh","Eighth","Ninth","Tenth","Eleventh",
            "Twelfth","Thirteenth","Fourteenth","Fifteenth",
            "Sixteenth","Seventeenth","Eighteenth","Nineteenth",
            "Twentieth","Twenty-first","Twenty-second"]

def ordinalAbbreviation(value, plural=False):
    '''Return the ordinal abbreviations for integers

    >>> from bbbalk import common
    >>> common.ordinalAbbreviation(3)
    'rd'
    >>> common.ordinalAbbreviation(255)
    'th'
    >>> common.ordinalAbbreviation(255, plural=True)
    'ths'

    :rtype: str
    '''
    valueHundreths = value % 100
    if valueHundreths in [11, 12, 13]:
        post = 'th'
    else:
        valueMod = value % 10
        if valueMod == 1:
            post = 'st'
        elif valueMod in [0, 4, 5, 6, 7, 8, 9]:
            post = 'th'
        elif valueMod == 2:
            post = 'nd'
        elif valueMod == 3:
            post = 'rd'

    if post != 'st' and plural:
        post += 's'
    return post

#----------------------------------
#-------------------------------------------------------------------------------
class Timer(object):
    """
    An object for timing. Call it to get the current time since starting.
    
    >>> t = common.Timer()
    >>> now = t()
    >>> nownow = t()
    >>> nownow > now
    True
    
    Call `stop` to stop it. Calling `start` again will reset the number
    
    >>> t.stop()
    >>> stopTime = t()
    >>> stopNow = t()
    >>> stopTime == stopNow
    True
    
    All this had better take less than one second!
    
    >>> stopTime < 1
    True
    """

    def __init__(self):
        # start on init
        self._tStart = time.time()
        self._tDif = 0
        self._tStop = None

    def start(self):
        '''Explicit start method; will clear previous values. Start always happens on initialization.'''
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

#------------------------
import multiprocessing
try:
    from concurrent import futures
except ImportError:  # only on Py3
    futures = None 
    
def multicore(func):
    '''
    Pseudo-decorator to run a function concurrently on multiple cores a list 
    or a list of tuples. Returns an iterator over the results
    
    (It is not a real decorator because they produce unpickleable functions.  Sad...)
    
    getGameHomeScore is defined in common as follows:
    
        def getGameHomeScore(gId):
             g = game.Game(gId)
             return gId, g.runs.home
    
    We can't put it in the docs because of pickle limitations.
    
    >>> import time
    >>> from bbbalk.common import getGameHomeScore, multicore
    >>> gameList = ['SDN201304090', 'SFN201409280', 'SLN201408140', 'SLN201408160', 'WAS201404250']
    >>> gFunc = multicore(getGameHomeScore)
    >>> t = time.time()
    >>> for gid, runs in gFunc(gameList):
    ...     print(gid, runs)
    SDN201304090 9
    SFN201409280 9
    SLN201408140 4
    SLN201408160 5
    WAS201404250 11
    >>> tDelta1 = time.time() - t
    
    Without multicore:
    
    >>> t = time.time()
    >>> for gid, runs in [getGameHomeScore(g) for g in gameList]:
    ...     unused = (gid, runs)
    >>> tDelta2 = time.time() - t
    >>> tDelta1 < tDelta2 * .9
    True
    
    All arguments and results need to be pickleable.  Pickleing a large object can be
    very slow! So use parallel processing only to pass small amounts of information
    back and forth (number of runs, etc.) if you return a Game or GameCollection object
    don't expect to see much speedup if any.
    '''
    max_workers = multiprocessing.cpu_count() - 1 # @UndefinedVariable
    if max_workers == 0:
        max_workers = 1
    
    def bg_f(argList):
        if len(argList) == 0:
            yield None
        firstArg = argList[0]
        argType = "unknown"
        if firstArg is None:
            argType = "none"
        elif isinstance(firstArg, (tuple, list)):
            argType = 'tuple'
        elif isinstance(firstArg, dict):
            argType = 'dict'
        else:
            argType = 'scalar'

        if futures is None:
            for i in argList:
                if argType == 'scalar':
                    yield func(i)
                elif argType == 'tuple':
                    yield func(*i)
        else:     

            with futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                if argType == 'scalar':
                    for res in executor.map(func, argList):
                        yield res
                elif argType == 'tuple':
                    for res in executor.map(func, *zip(*argList)):
                        yield res
                else:
                    raise BBBalkException('Cannot Parallelize arguments of type {0}'.format(argType))
        
    return bg_f


def getGameHomeScore(gId):
    from bbbalk import game # @UnresolvedImport
    g = game.Game(gId)
    return gId, g.runs.home


def runDemo(team):
    from bbbalk import game # @UnresolvedImport
    gc = game.GameCollection()
    gc.team = team
    gc.parse()
    if team == 'BOS':
        time.sleep(4)
    return team, len(gc.games)

def runDemo2(team, year):
    from bbbalk import game # @UnresolvedImport
    gc = game.GameCollection()
    gc.team = team
    gc.yearStart = year
    gc.yearEnd = year
    gc.parse()
    if team == 'BOS':
        time.sleep(4)
    return team, len(gc.games)


#------------------------


class SlottedObject(object):
    r'''
    Provides template for classes implementing slots allowing it to be pickled
    properly.
    
    Only use SlottedObjects for objects that we expect to make so many of
    that memory storage and speed become an issue. For instance an object representing
    a single play or plate appearence.
    
    >>> import pickle
    >>> class BatAngle(common.SlottedObject):
    ...     __slots__ = ('horizontal', 'vertical')
    >>> s = BatAngle()
    >>> s.horizontal = 35
    >>> s.vertical = 20
    >>> #_DOCS_SHOW out = pickle.dumps(s)
    >>> #_DOCS_SHOW t = pickle.loads(out)
    >>> t = s #_DOCS_HIDE -- cannot define classes for pickling in doctests
    >>> t.horizontal, t.vertical
    (35, 20)
    '''
    
    ### CLASS VARIABLES ###

    __slots__ = ()

    ### SPECIAL METHODS ###

    def __getstate__(self):
        if getattr(self, '__dict__', None) is not None:
            state = getattr(self, '__dict__').copy()
        else:
            state = {}
        slots = set()
        for cls in self.__class__.mro():
            slots.update(getattr(cls, '__slots__', ()))
        for slot in slots:
            sValue = getattr(self, slot, None)
            if type(sValue) is weakref.ref:
                sValue = sValue()
                print("Warning: uncaught weakref found in %r - %s, will not be rewrapped" % (self, slot))
            state[slot] = sValue
        if getattr(self, '__dict__', None) is not None:
            print("We got a dict TOO!", getattr(self, '__class__')) 
        return state

    def __setstate__(self, state):
        #print("Restoring state {0}".format(self.__class__))
        for slot, value in state.items():
            setattr(self, slot, value)

class ParentType(SlottedObject):

    __slots__ = ('_parent',)
    
    def __init__(self, parent=None):
        self._parent = None
        self.parent = parent

    def __getstate__(self):
        pValue = getattr(self, '_parent', None)
        setattr(self, '_parent', None)
        state = super(ParentType, self).__getstate__()
        state['_parent'] = pValue
        return state

    def __setstate__(self, state):
        super(ParentType, self).__setstate__(state)
        pValue = getattr(self, '_parent', None)
        try:
            pValue = weakref.ref(pValue)
        except TypeError:
            pass # hardref now...
        setattr(self, '_parent', pValue)
        
    def parentByClass(self, className):
        '''
        iterate through parents until one of the proper class is found.
        '''
        p = self.parent
        if p is None:
            return None
        if p.__class__.__name__ == className:
            return p
        elif hasattr(p, 'parentByClass'):
            return p.parentByClass(className)
        else:
            return None

    def _getParent(self):
        if type(self._parent) is weakref.ref:
            return self._parent()
        else:
            return self._parent
        
    def _setParent(self, referent):
        try:
            self._parent = weakref.ref(referent)
        # if referent is None, will raise a TypeError
        # if referent is a weakref, will also raise a TypeError
        # will also raise a type error for string, ints, etc.
        # slight performance bost rather than checking if None
        except TypeError:
            self._parent = referent
    
    parent = property(_getParent, _setParent)

#-------------------------------------------------------------------------------
def wrapWeakref(referent):
    '''
    utility function that wraps objects as weakrefs but does not wrap
    already wrapped objects; also prevents wrapping the unwrapable "None" type, etc.

    >>> import weakref
    >>> class Mock(object):
    ...     pass
    >>> a1 = Mock()
    >>> ref1 = common.wrapWeakref(a1)
    >>> ref1
    <weakref at 0x101f29ae8; to 'Mock' at 0x101e45358>
    >>> ref2 = common.wrapWeakref(ref1)
    >>> ref2
    <weakref at 0x101f299af; to 'Mock' at 0x101e45358>
    >>> ref3 = common.wrapWeakref(5)
    >>> ref3
    5
    '''
    #if type(referent) is weakref.ref:
#     if isinstance(referent, weakref.ref):
#         return referent
    try:
        return weakref.ref(referent)
    # if referent is None, will raise a TypeError
    # if referent is a weakref, will also raise a TypeError
    # will also raise a type error for string, ints, etc.
    # slight performance boost rather than checking if None
    except TypeError:
        return referent

def unwrapWeakref(referent):
    '''
    Utility function that gets an object that might be an object itself
    or a weak reference to an object.  It returns obj() if it's a weakref or another callable.
    and obj if it's not.

    >>> class Mock(object):
    ...     pass
    >>> a1 = Mock()
    >>> a2 = Mock()
    >>> a2.strong = a1
    >>> a2.weak = common.wrapWeakref(a1)
    >>> common.unwrapWeakref(a2.strong) is a1
    True
    >>> common.unwrapWeakref(a2.weak) is a1
    True
    >>> common.unwrapWeakref(a2.strong) is common.unwrapWeakref(a2.weak)
    True
    '''
    try:
        return referent()
    except TypeError:
        return referent


def keyword_only_args(*included_keywords):
    """Transforms a function with keyword arguments into one with
    keyword-only arguments.

    Call this decorator as @keyword_only_args() for the default mode,
    which makes all keyword arguments keyword-only, or with the names
    of arguments to make keyword-only.  They must correspond with the
    names of arguments in the decorated function.  It works by
    collecting all the arguments into *args and **kws, then moving the
    arguments marked as keyword-only from **kws into *args.

    From Cara at:
    http://code.activestate.com/recipes/578993-keyword-only-arguments-in-python-2x/
    Revision 8, MIT license
    Modified slightly -- my version works fine with keywords specified and defaulting to defaults
       but does not yet work with *args TODO: Make it work, see basic.

    Args:
      *included_keywords: Keyword-only arguments as strings.

    Returns:
      A decorator that modifies a function so it has keyword-only
      arguments.

    """
    def decorator(func):
        """Decorator factory, assigns arguments as keyword-only and
        calculates sets for error checking.

        Args:
          func: The function to decorate.

        Returns:
          A function wrapped so that it has keyword-only arguments. 
        """
        # we want to preserve default=None, so we need to give a very implausible value for a default
        noDefaultString = '***NO_DEFAULT_PROVIDED***'
        # do not use getfullargspec -- if we had it we wouldnt need this
        positional_args, unused_varargs, unused_keywords, defaults = inspect.getargspec(func) 
        args_with_defaults = set(positional_args[len(positional_args) - len(defaults):])
        
        kw_only_args = set(included_keywords) if len(included_keywords) > 0 else args_with_defaults.copy()
        args_and_defaults = list(zip_longest(reversed(positional_args), reversed(defaults), fillvalue=noDefaultString))
        args_and_defaults.reverse()
        #warn(args_and_defaults)
        positional_args = set(positional_args)

        @functools.wraps(func)
        def wrapper(*callingArgs, **keywordDict):
            """The decorator itself, checks arguments with set operations, moves
            args from *args into **kws, and then calls func().

            Args:
              *args, **kws: The arguments passed to the original function.

            Returns:
              The original function's result when it's called with the
              modified arguments.

            Raises:
              TypeError: When there is a mismatch between the supplied
                and expected arguments.

            """
            keywordSet = set(keywordDict)
            # Are all the keyword-only args covered either by a passed
            # argument or a default?
            kw_only_args_specified_by_keyword_or_default = keywordSet | args_with_defaults
            if not kw_only_args <= kw_only_args_specified_by_keyword_or_default:
                missing_args = kw_only_args - kw_only_args_specified_by_keyword_or_default
                wrong_args(func, args_and_defaults, missing_args, 'keyword-only')
            # Are there enough positional args to cover all the
            # arguments not covered by a passed argument or a default?
            if len(callingArgs) < len(positional_args - kw_only_args_specified_by_keyword_or_default):
                missing_args = positional_args - kw_only_args_specified_by_keyword_or_default
                wrong_args(func, args_and_defaults, missing_args, 'positional', len(callingArgs))

            #positional_args_specified_by_keyword = keywordSet & positional_args
            
            finalArgs = []
            maxIndex = 0
            for index, (name, default) in enumerate(args_and_defaults):
                #warn(index, name, default)
                fArg = noDefaultString
                if name in keywordDict:
                    fArg = keywordDict[name]
                    #warn("Got non-default for name ", name, " value: ", fArg)
                    keywordDict.pop(name)
                else:
                    if maxIndex < len(callingArgs):
                        fArg = callingArgs[maxIndex]
                        maxIndex += 1
                        #warn("Got positional argument for name ", name, " value: ", fArg)

                    elif name not in keywordDict and default is not noDefaultString:
                        fArg = default
                        #warn("Got default for name ", name, " default: ", repr(default))
                                            
                if fArg is not noDefaultString:
                    finalArgs.append(fArg)
            if len(callingArgs) > maxIndex: #  *args                
                finalArgs.extend(callingArgs[maxIndex:])
            #warn(callingArgs[1:])
            #warn(finalArgs[1:])
            #warn(args_and_defaults)
                
            #warn("function ", func, " originally called with (after self) ", callingArgs[1:], " will be called with args (after self):", finalArgs[1:], " and **keywords", keywordDict)
            return func(*finalArgs, **keywordDict)
        return wrapper

    def wrong_args(func, args_and_defaults, missing_args, arg_type, number_of_args=0):
        """ Raise Python 3-style TypeErrors for missing arguments."""
        ordered_args = [a for a, _ in args_and_defaults if a in missing_args]
        ordered_args = ordered_args[number_of_args:]
        error_message = ['%s() missing %d required %s argument' % (func.__name__, len(ordered_args), arg_type)]
        if len(ordered_args) == 1:
            error_message.append(": '%s'" % ordered_args[0])
        else:
            error_message.extend(['s: ', ' '.join("'%s'" % a for a in ordered_args[:-1]), " and '%s'" % ordered_args[-1]])
        raise TypeError(''.join(error_message))

    return decorator

def warn(*msg):
    '''
    To print a warning to the user, send a list of strings to this method.
    Similar to printDebug but even if debug is off.
    '''
    msg = formatStr(msg)
    sys.stderr.write(msg)

def formatStr(msg, *arguments, **keywords):
    '''Format one or more data elements into string suitable for printing
    straight to stderr or other outputs

    >>> a = common.formatStr('test', '1', 2, 3)
    >>> print(a)
    test 1 2 3
    <BLANKLINE>
    '''
    if 'format' in keywords:
        formatType = keywords['format']
    else:
        formatType = None

    msg = [msg] + list(arguments)
    if six.PY3:
        for i in range(len(msg)):
            x = msg[i]
            if isinstance(x, bytes): 
                msg[i] = x.decode('utf-8')
            if not isinstance(x, str):
                try:
                    msg[i] = repr(x)
                except TypeError:
                    try:
                        msg[i] = x.decode('utf-8')
                    except AttributeError:
                        msg[i] = "<__repr__ failed for " + x.__class__.__name__ + ">"
                except AttributeError: # or something
                    msg[i] = "<__repr__ failed for " + x.__class__.__name__ + ">"
    else:
        msg = [str(x) for x in msg]
    if formatType == 'block':
        return '\n*** '.join(msg)+'\n'
    else: # catch all others
        return ' '.join(msg)+'\n'

if __name__ == '__main__':
    import bbbalk
    bbbalk.mainTest()