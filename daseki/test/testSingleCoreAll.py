# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         test.py
# Purpose:      Controller for all module tests in daseki.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2016 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------
'''
Controller to run all module tests in the daseki folders.

Runs great, but slowly on multiprocessor systems.
'''

import doctest
import sys
import unittest
import warnings

from daseki import common

from daseki.test import testRunner
from daseki.test import commonTest

from daseki.test import coverageDS
cov = coverageDS.getCoverage()



def main(testGroup=('test',), restoreEnvironmentDefaults=False, limit=None):
    '''Run all tests. Group can be test and external

    >>> print(None)
    None
    '''
    s1 = commonTest.defaultDoctestSuite(__name__)

    modGather = commonTest.ModuleGather()
    modules = modGather.load(restoreEnvironmentDefaults)

    verbosity = 2
    if 'verbose' in sys.argv:
        verbosity = 1  # this seems to hide most display

    # print('looking for Test classes...\n')
    # look over each module and gather doc tests and unittests
    totalModules = 0

    for moduleObject in common.sortModules(modules):
        unitTestCases = []
        if limit is not None:
            if totalModules > limit:
                break
        totalModules += 1
        # get Test classes in module
        if not hasattr(moduleObject, 'Test'):
            pass
            # print('%s has no Test class' % moduleObject)
        else:
            if 'test' in testGroup:
                unitTestCases.append(moduleObject.Test)
        if not hasattr(moduleObject, 'TestExternal'):
            pass
            # environLocal.printDebug('%s has no TestExternal class\n' % module)
        else:
            if 'external' in testGroup or 'testExternal' in testGroup:
                unitTestCases.append(moduleObject.TestExternal)

        # for each Test class, load this into a suite
        for testCase in unitTestCases:
            s2 = unittest.defaultTestLoader.loadTestsFromTestCase(testCase)
            s1.addTests(s2)
        try:
            s3 = commonTest.defaultDoctestSuite(moduleObject)
            s1.addTests(s3)
        except ValueError:
            print(f'{moduleObject} cannot load Doctests')
            continue

        allLocals = [getattr(moduleObject, x) for x in dir(moduleObject)]

        globs = __import__('daseki').__dict__.copy()
        docTestOptions = (doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)
        testRunner.addDocAttrTestsToSuite(s1,
                                          allLocals,
                                          outerFilename=moduleObject.__file__,
                                          globs=globs,
                                          optionflags=docTestOptions,
                                          # no checker here
                                          )

    testRunner.fixTestsForPy2and3(s1)

    # print('running Tests...\n')

    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)  # import modules...
        runner = unittest.TextTestRunner(verbosity=verbosity)
        finalTestResults = runner.run(s1)

    coverageDS.stopCoverage(cov)

    if (finalTestResults.errors or
            finalTestResults.failures or
            finalTestResults.unexpectedSuccesses):
        returnCode = 1
    else:
        returnCode = 0

    return returnCode



def travisMain():
    # exits with the returnCode
    returnCode = main()
    exit(returnCode)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # if optional command line arguments are given, assume they are
    # test group arguments
    if len(sys.argv) >= 2:
        returnCode = main(sys.argv[1:])
    else:
        returnCode = main()
