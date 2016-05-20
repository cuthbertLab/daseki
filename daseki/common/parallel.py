#-*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         common/parallel.py
# Purpose:      Utilities for parallel computing
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015-16 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
#-------------------------------------------------------------------------------
__all__ = ['runParallel',
           'runNonParallel',
           'cpus',
           'multicore',
           ]

import multiprocessing
import time
from concurrent import futures

from daseki.exceptionsDS import DasekiException
from daseki.ext.joblib import Parallel, delayed  # @UnresolvedImport

def runParallel(iterable, parallelFunction, 
                updateFunction=None, updateMultiply=3,
                unpackIterable=False):
    '''
    runs parallelFunction over iterable in parallel, optionally calling updateFunction after
    each common.cpus * updateMultiply calls.
    
    Setting updateMultiply too small can make it so that cores wait around when they
    could be working if one CPU has a particularly hard task.  Setting it too high
    can make it seem like the job has hung.

    updateFunction should take three arguments: the current position, the total to run,
    and the most recent results.  It does not need to be pickleable, and in fact,
    a bound method might be very useful here.  Or updateFunction can be "True"
    which just prints a generic message.

    If unpackIterable is True then each element in iterable is considered a list or
    tuple of different arguments to delayFunction.

    Partial functions are pickleable, so if you need to pass the same
    arguments to parallelFunction each time, make it a partial function before passing
    it to runParallel.

    Note that parallelFunction, iterable's contents, and the results of calling parallelFunction
    must all be pickleable, and that if pickling the contents or
    unpickling the results takes a lot of time, you won't get nearly the speedup
    from this function as you might expect.  
    '''
    iterLength = len(iterable)
    totalRun = 0
    numCpus = cpus()
    
    resultsList = []
    
    if multiprocessing.current_process().daemon: # @UndefinedVariable
        return runNonParallel(iterable, parallelFunction, updateFunction,
                              updateMultiply, unpackIterable)
    
    with Parallel(n_jobs=numCpus) as para:
        delayFunction = delayed(parallelFunction)
        while totalRun < iterLength:
            endPosition = min(totalRun + numCpus * updateMultiply, iterLength)
            rangeGen = range(totalRun, endPosition)
            
            if unpackIterable:
                _r = para(delayFunction(*iterable[i]) for i in rangeGen)
            else:
                _r = para(delayFunction(iterable[i]) for i in rangeGen)

            totalRun = endPosition
            resultsList.extend(_r)
            if updateFunction is True:
                print("Done {} tasks of {}".format(totalRun, iterLength))
            elif updateFunction is not None:
                updateFunction(totalRun, iterLength, _r)


    return resultsList


def runNonParallel(iterable, parallelFunction, 
                updateFunction=None, updateMultiply=3,
                unpackIterable=False):
    '''
    This is intended to be a perfect drop in replacement for runParallel, except that
    it runs on one core only, and not in parallel.
    
    Used, for instance, if we're already in a parallel function.
    '''
    iterLength = len(iterable)
    resultsList = []

    for i in range(iterLength):
        if unpackIterable:
            _r = parallelFunction(*iterable[i])
        else:
            _r = parallelFunction(iterable[i])
        
        resultsList.append(_r)
            
        if updateFunction is True and i % updateMultiply == 0:
            print("Done {} tasks of {} not in parallel".format(i, iterLength))
        elif updateFunction is not None and i % updateMultiply == 0:
            updateFunction(i, iterLength, [_r])
        
    return resultsList
    

def cpus():
    '''
    Returns the number of CPUs or if >= 3, one less (to leave something out for multiprocessing)
    '''
    cpuCount = multiprocessing.cpu_count() # @UndefinedVariable
    if cpuCount >= 3:
        return cpuCount - 1
    else:
        return cpuCount

# Not shown to work.
# def pickleCopy(obj):
#     '''
#     use pickle to serialize/deserialize a copy of an object -- much faster than deepcopy,
#     but only works for things that are completely pickleable.
#     '''
#     return pickleMod.loads(pickleMod.dumps(obj, protocol=-1))

def demo_GameHomeScore(gId):
    '''
    
    '''
    from daseki import game # @UnresolvedImport
    g = game.Game(gId)
    return gId, g.runs.home


def multicore(func):
    '''
    Pseudo-decorator to run a function concurrently on multiple cores a list 
    or a list of tuples. Returns an iterator over the results
    
    (It is not a real decorator because they produce unpickleable functions.  Sad...)
    
    demo_GameHomeScore is defined in common as follows:
    
        def demo_GameHomeScore(gId):
             g = game.Game(gId)
             return gId, g.runs.home
    
    We can't put it in the docs because of pickle limitations.
    
    >>> import time
    >>> from daseki.common.parallel import demo_GameHomeScore, multicore
    >>> gameList = ['SDN201304090', 'SFN201409280', 'SLN201408140', 'SLN201408160', 'WAS201404250']
    >>> gFunc = multicore(demo_GameHomeScore)
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
    >>> for gid, runs in [demo_GameHomeScore(g) for g in gameList]:
    ...     unused = (gid, runs)
    >>> tDelta2 = time.time() - t
    >>> tDelta1 < tDelta2 * .9
    True
    
    All arguments and results need to be pickleable.  Pickleing a large object can be
    very slow! So use parallel processing only to pass small amounts of information
    back and forth (number of runs, etc.) if you return a Game or GameCollection object
    don't expect to see much speedup if any.
    '''
    max_workers = cpus() # @UndefinedVariable

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
                    raise DasekiException(
                        'Cannot Parallelize arguments of type {0}'.format(argType))        
    return bg_f


def runDemo(team):
    from daseki import game # @UnresolvedImport
    gc = game.GameCollection()
    gc.team = team
    gc.parse()
    if team == 'BOS':
        time.sleep(4)
    return team, len(gc.games)

def runDemo2(team, year):
    from daseki import game # @UnresolvedImport
    gc = game.GameCollection()
    gc.team = team
    gc.yearStart = year
    gc.yearEnd = year
    gc.parse()
    if team == 'BOS':
        time.sleep(4)
    return team, len(gc.games)


if __name__ == "__main__":
    import daseki
    daseki.mainTest()

#------------------------------------------------------------------------------
# eof
