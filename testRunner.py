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

import sys
import unittest
import doctest
from bbbalk.ext import six


def mainTest(*testClasses, **kwargs):
    '''
    Takes as its arguments modules (or a string 'noDocTest' or 'verbose')
    and runs all of these modules through a unittest suite

    Unless 'noDocTest' is passed as a module, a docTest
    is also performed on `__main__`, hence the name "mainTest".

    If 'moduleRelative' (a string) is passed as a module, then
    global variables are preserved.

    Run example (put at end of your modules):

    ::

        import unittest
        class Test(unittest.TestCase):
            def testHello(self):
                hello = "Hello"
                self.assertEqual("Hello", hello)

        import bbbalk
        if __name__ == '__main__':
            bbbalk.mainTest(Test)

    '''
    #environLocal.printDebug(['mainTest()', testClasses])

    runAllTests = True

    # start with doc tests, then add unit tests
    if ('noDocTest' in testClasses or 'noDocTest' in sys.argv
        or 'nodoctest' in sys.argv):
        # create a test suite for storage
        s1 = unittest.TestSuite()
    else:
        # create test suite derived from doc tests
        # here we use '__main__' instead of a module
        failFast = bool(kwargs.get('failFast', True))
        if failFast:
            optionflags = (
                doctest.ELLIPSIS |
                doctest.NORMALIZE_WHITESPACE |
                doctest.REPORT_ONLY_FIRST_FAILURE
                )
        else:
            optionflags = (
                doctest.ELLIPSIS |
                doctest.NORMALIZE_WHITESPACE
                )
        if 'moduleRelative' in testClasses or 'moduleRelative' in sys.argv:
            s1 = doctest.DocTestSuite(
                '__main__',
                optionflags=optionflags,
                )
        else:
            globs = __import__('bbbalk').__dict__.copy()
            s1 = doctest.DocTestSuite(
                '__main__',
                globs=globs,
                optionflags=optionflags,
                )

    verbosity = 1
    if 'verbose' in testClasses or 'verbose' in sys.argv:
        verbosity = 2 # this seems to hide most display

    displayNames = False
    if 'list' in sys.argv or 'display' in sys.argv:
        displayNames = True
        runAllTests = False

    runThisTest = None
    if len(sys.argv) == 2:
        arg = sys.argv[1].lower()
        if arg not in ['list', 'display', 'verbose', 'nodoctest']:
            # run a test directly named in this module
            runThisTest = sys.argv[1]

    # -f, --failfast
    if 'onlyDocTest' in sys.argv or 'onlyDocTest' in testClasses:
        testClasses = [] # remove cases
    for t in testClasses:
        if not isinstance(t, six.string_types):
            if displayNames is True:
                for tName in unittest.defaultTestLoader.getTestCaseNames(t):
                    print('Unit Test Method: %s' % tName)
            if runThisTest is not None:
                tObj = t() # call class
                # search all names for case-insensitive match
                for name in dir(tObj):
                    if name.lower() == runThisTest.lower() or \
                         name.lower() == ('test' + runThisTest.lower()) or \
                         name.lower() == ('xtest' + runThisTest.lower()):
                        runThisTest = name
                        break
                if hasattr(tObj, runThisTest):
                    print('Running Named Test Method: %s' % runThisTest)
                    getattr(tObj, runThisTest)()
                    runAllTests = False
                    break
                else:
                    print('Could not find named test method: %s, running all tests' % runThisTest)

            # normally operation collects all tests
            s2 = unittest.defaultTestLoader.loadTestsFromTestCase(t)
            s1.addTests(s2)


    if runAllTests is True:
        if six.PY3: # correct "BBBException" to "...BBBException"
            for dtc in s1: # Suite to DocTestCase
                if hasattr(dtc, '_dt_test'):
                    dt = dtc._dt_test # DocTest
                    for example in dt.examples:
                        if example.exc_msg is not None and len(example.exc_msg) > 0:
                            example.exc_msg = "..." + example.exc_msg[1:]
                        elif (example.want is not None and
                                example.want.startswith('u\'')):
                                    # probably a unicode example:
                                    # simplistic, since (u'hi', u'bye')
                                    # won't be caught, but saves a lot of anguish
                                example.want = example.want[1:]
                        
        runner = unittest.TextTestRunner()
        runner.verbosity = verbosity
        unused_testResult = runner.run(s1)
