# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         common.py
# Purpose:      Commonly used tools across Daseki
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2014-16 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
# ----------------------------------------------------------------------------
'''
Common is a collection of utility functions, objects, constants and dictionaries used
throughout daseki.

functions in common/ should not import anything from daseki except daseki.exceptionsDS
(except in tests and doctests).

For historical reasons all the (non-private) functions etc. of the common/
folder are available by importing common.
'''

# pylint: disable=wildcard-import
from typing import Any

from daseki.common.parallel import *

import enum
import inspect
import re
import os
import sys
import time
import tempfile
import weakref

from daseki.exceptionsDS import DasekiException

maxRetrosheetYear = 2015


class TeamNum(enum.IntEnum):
    VISITOR = 0
    HOME = 1


# tools for setup.py
def sourceFilePath():
    '''
    Get the Daseki directory that contains source files. This is not the same as the
    outermost package development directory.
    '''
    dn = os.path.dirname
    fpThis = inspect.getfile(sourceFilePath)
    fpDS = dn(dn(fpThis))
    # use retro as a test case
    if 'retro' not in os.listdir(fpDS):
        raise DasekiException('cannot find expected daseki directory: %s' % fpDS)
    return fpDS


def dataFilePath():
    return os.path.join(sourceFilePath(), 'dataFiles')


def dataRetrosheet():
    return os.path.join(dataFilePath(), 'retrosheet')


def dataRetrosheetEvent():
    return os.path.join(dataRetrosheet(), 'event')


def dataRetrosheetByType(gameType='regular'):
    if gameType not in ('asg', 'post', 'regular'):
        raise DasekiException('gameType must be asg, post, or regular, not {0}'.format(gameType))
    return os.path.join(dataRetrosheetEvent(), gameType)


def gameLogFilePath():
    return os.path.join(dataRetrosheet(), 'gamelog')


# ---------------------
def getDefaultRootTempDir():
    '''
    returns whatever tempfile.gettempdir() returns plus 'daseki'.

    Creates the subdirectory if it doesn't exist:

    >>> from daseki import common
    >>> import tempfile
    >>> t = tempfile.gettempdir()
    >>> #_DOCS_SHOW t
    '/var/folders/x5/rymq2tx16lqbpytwb1n_cc4c0000gn/T'

    >>> import os
    >>> common.getDefaultRootTempDir() == os.path.join(t, 'daseki')
    True
    '''
    # this returns the root temp dir; this does not create a new dir
    dstDir = os.path.join(tempfile.gettempdir(), 'daseki')
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


# ---------------------
GAMEID_MATCH = re.compile(r'([A-Za-z][A-Za-z][A-Za-z])(\d\d\d\d)(\d\d)(\d\d)(\d?)')


class GameId(object):
    '''
    A GameId is a 12-character string that embeds information about
    when and where a game was played.  It is designed to uniquely identify
    any game every played.

    We can initialize a GameId object from a string:

    >>> from daseki import common
    >>> gid = common.GameId('SDN201304090')
    >>> str(gid)
    'SDN201304090'
    >>> gid
    <daseki.common.GameId SDN201304090>
    >>> gid.year
    2013
    >>> gid.day
    9
    >>> gid.gameNum  # always a string because of weird split double header A, B codes
    '0'
    >>> gid.homeTeam
    'SDN'

    Or we can construct the id from all the information:

    >>> gid2 = common.GameId()
    >>> gid2.homeTeam = 'ARI'
    >>> gid2.year = 2000
    >>> gid2.month = 9
    >>> gid2.day = 22
    >>> print(gid2)
    ARI200009220

    Last digit is optional:

    >>> gid = common.GameId('SDN20130409')
    >>> str(gid)
    'SDN201304090'
    '''
    def __init__(self, gameId=None):
        self.gameId = gameId
        self.year = 0
        self.month = 0
        self.day = 0
        self.gameNum = '0'
        self.homeTeam = 'XXX'
        if gameId is not None:
            self.parse()

    def __repr__(self):
        return '<{0}.{1} {2}>'.format(self.__module__, self.__class__.__name__, str(self))

    def __str__(self):
        return '{s.homeTeam}{s.year:4d}{s.month:02d}{s.day:02d}{s.gameNum}'.format(s=self)


    def parse(self):
        gameId = self.gameId
        matched = GAMEID_MATCH.match(gameId)
        if not matched:
            raise DasekiException('invalid gameId: %s' % gameId)
        self.homeTeam = matched.group(1).upper()
        self.year = int(matched.group(2))
        self.month = int(matched.group(3))
        self.day = int(matched.group(4))
        self.gameNum = matched.group(5)
        if self.gameNum == '':
            self.gameNum = '0'


# ---------------------
ordinals = ['Zeroth', 'First', 'Second', 'Third', 'Fourth', 'Fifth',
            'Sixth', 'Seventh', 'Eighth', 'Ninth', 'Tenth', 'Eleventh',
            'Twelfth', 'Thirteenth', 'Fourteenth', 'Fifteenth',
            'Sixteenth', 'Seventeenth', 'Eighteenth', 'Nineteenth',
            'Twentieth', 'Twenty-first', 'Twenty-second']


def ordinalAbbreviation(value, plural=False):
    '''Return the ordinal abbreviations for integers

    >>> from daseki import common
    >>> common.ordinalAbbreviation(3)
    'rd'
    >>> common.ordinalAbbreviation(255)
    'th'
    >>> common.ordinalAbbreviation(255, plural=True)
    'ths'

    :rtype: str
    '''
    valueHundreths = value % 100
    post = ''
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


# -------------------------------------------------------------------------------
class Timer(object):
    '''
    An object for timing. Call it to get the current time since starting.

    >>> from daseki import common
    >>> t = common.Timer()
    >>> now = t()
    >>> now_now = t()
    >>> now_now > now
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
    '''

    def __init__(self):
        # start on init
        self._tStart = time.time()
        self._tDif = 0
        self._tStop = None

    def start(self):
        '''
        Explicit start method; will clear previous values.
        Start always happens on initialization.
        '''
        self._tStart = time.time()
        self._tStop = None  # show that a new run has started so __call__ works
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
        if self._tStop is None:  # if not stopped yet
            t = time.time() - self._tStart
        else:
            t = self._tDif
        return t

    def __str__(self):
        if self._tStop is None:  # if not stopped yet
            t = time.time() - self._tStart
        else:
            t = self._tDif
        return str(round(t, 3))


# ---------
def sortModules(moduleList):
    '''
    Sort a lost of imported module names such that most recently modified is
    first.  In ties, last access time is used then module name

    Will return a different order each time depending on the last mod time

    :rtype: list(str)
    '''
    sort = []
    modNameToMod = {}
    for mod in moduleList:
        modNameToMod[mod.__name__] = mod
        fp = mod.__file__  # returns the pyc file
        stat = os.stat(fp)
        lastmod = time.localtime(stat[8])
        asctime = time.asctime(lastmod)
        sort.append((lastmod, asctime, mod.__name__))
    sort.sort()
    sort.reverse()
    # just return module list
    return [modNameToMod[modName] for lastmod, asctime, modName in sort]


# ------------------------
class SlottedObjectMixin(object):
    r'''
    Provides template for classes implementing slots allowing it to be pickled
    properly.

    Only use SlottedObjects for objects that we expect to make so many of
    that memory storage and speed become an issue. For instance an object representing
    a single play or plate appearence.

    >>> import pickle
    >>> from daseki import common
    >>> class BatAngle(common.SlottedObjectMixin):
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

    # CLASS VARIABLES #

    __slots__ = ('__weakref__')

    # SPECIAL METHODS #

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
            if isinstance(sValue, weakref.ref):
                sValue = sValue()
                print('Warning: uncaught weakref found in %r - %s, will not be rewrapped' %
                      (self, slot))
            state[slot] = sValue
        if getattr(self, '__dict__', None) is not None:
            print('We got a dict TOO!', getattr(self, '__class__'))
        return state

    def __setstate__(self, state):
        # print('Restoring state {0}'.format(self.__class__))
        for slot, value in state.items():
            setattr(self, slot, value)


class ParentMixin(SlottedObjectMixin):
    __slots__ = ('_parent',)

    def __init__(self, parent=None):
        self._parent = None
        if parent is not None:
            self.parent = parent

    def __getstate__(self):
        pValue = getattr(self, '_parent', None)
        setattr(self, '_parent', None)
        state = super().__getstate__()
        state['_parent'] = pValue
        return state

    def __setstate__(self, state):
        super().__setstate__(state)
        pValue = getattr(self, '_parent', None)
        try:
            pValue = weakref.ref(pValue)
        except TypeError:
            pass  # hard reference now...
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
        _p = self._parent
        if _p is None:
            return _p
        elif isinstance(_p, weakref.ref):
            return _p()
        else:
            return _p

    def _setParent(self, referent):
        if referent is None:
            return
        try:
            self._parent = weakref.ref(referent)
        # if referent is None, will raise a TypeError
        # if referent is a weakref, will also raise a TypeError
        # will also raise a type error for string, ints, etc.
        # slight performance boost rather than checking if None
        except TypeError:
            self._parent = referent

    parent = property(_getParent, _setParent)


# ------------------------------------------------------------------------------
def wrapWeakref(referent):
    '''
    utility function that wraps objects as weakrefs but does not wrap
    already wrapped objects; also prevents wrapping the unwrapable 'None' type, etc.

    >>> import weakref
    >>> from daseki import common
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
    # if type(referent) is weakref.ref:
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

    >>> from daseki import common
    >>> class Mock(object):
    ...     strong: Any
    ...     weak: Any
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

    >>> from daseki import common
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
                    msg[i] = '<__repr__ failed for ' + x.__class__.__name__ + '>'
            except AttributeError:  # or something
                msg[i] = '<__repr__ failed for ' + x.__class__.__name__ + '>'

    if formatType == 'block':
        return '\n*** '.join(msg)+'\n'
    else:  # catch all others
        return ' '.join(msg)+'\n'


if __name__ == '__main__':
    import daseki
    daseki.mainTest()
