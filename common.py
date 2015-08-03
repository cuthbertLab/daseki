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

import functools
import inspect
import sys
import os
import weakref
from bbbalk.ext import six
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

def dataDirByYear(year=2014):
    return os.path.join(dataFilePath(), str(year)) + 'eve'

ordinals = ["Zeroth","First","Second","Third","Fourth","Fifth",
            "Sixth","Seventh","Eighth","Ninth","Tenth","Eleventh",
            "Twelfth","Thirteenth","Fourteenth","Fifteenth",
            "Sixteenth","Seventeenth","Eighteenth","Nineteenth",
            "Twentieth","Twenty-first","Twenty-second"]

def ordinalAbbreviation(value, plural=False):
    '''Return the ordinal abbreviations for integers

    >>> from music21 import common
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
    >>> s = Glissdata
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
        state = {}
        slots = set()
        for cls in self.__class__.mro():
            slots.update(getattr(cls, '__slots__', ()))
        for slot in slots:
            sValue = getattr(self, slot, None)
            if sValue is not None and type(sValue) is weakref.ref:
                sValue = sValue()
                print("Warning: uncaught weakref found in %r - %s, will not be rewrapped" % (self, slot))
            state[slot] = sValue
        return state

    def __setstate__(self, state):
        for slot, value in state.items():
            setattr(self, slot, value)

class ParentType(SlottedObject):
    __slots__ = ('_parent')
    
    def __init__(self, parent=None):
        self._parent = None
        self.parent = parent

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
    print(dataDirByYear(2012))
