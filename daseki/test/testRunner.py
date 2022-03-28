# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         testRunner.py
# Purpose:      runs tests on any system
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2014-15 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
'''
The testRunner module contains the all important 'mainTest' function that runs tests
in a given module.  Except for the one instance of 'defaultImports', everything here
can run on any system, not just music21.
'''
import doctest
import inspect
import re
import sys
import unittest

defaultImports = ('daseki',)


# test related functions
def addDocAttrTestsToSuite(
    suite,
    moduleVariableLists,
    outerFilename=None,
    globs=False,
    optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE
):
    # noinspection PyProtectedMember,PyUnresolvedReferences
    '''
    takes a suite, such as a doctest.DocTestSuite and the list of variables
    in a module and adds from those classes that have a _DOC_ATTR dictionary
    (which documents the properties in the class) any doctests to the suite.

    >>> import doctest

    >>> from daseki import game, test
    >>> s1 = doctest.DocTestSuite(game)
    >>> s1TestsBefore = len(s1._tests)
    >>> allLocals = [getattr(game, x) for x in dir(game)]
    >>> test.testRunner.addDocAttrTestsToSuite(s1, allLocals)
    >>> s1TestsAfter = len(s1._tests)
    >>> s1TestsAfter - s1TestsBefore
    1
    >>> t = s1._tests[-1]
    >>> t
    park ()
    '''
    dtp = doctest.DocTestParser()
    if globs is False:
        globs = __import__(defaultImports[0]).__dict__.copy()
    for lvk in moduleVariableLists:
        if not (inspect.isclass(lvk)):
            continue
        docattr = getattr(lvk, '_DOC_ATTR', None)
        if docattr is None:
            continue
        for dockey in docattr:
            documentation = docattr[dockey]
            # print(documentation)
            dt = dtp.get_doctest(documentation, globs, dockey, outerFilename, 0)
            if len(dt.examples) == 0:
                continue
            dtc = doctest.DocTestCase(dt, optionflags=optionflags)
            # print(dtc)
            suite.addTest(dtc)


def fixTestsForPy2and3(doctestSuite):
    '''
    Fix doctests so that they work in both python2 and python3, namely
    unicode/byte characters and added module names to exceptions.

    >>> import doctest
    >>> from daseki import game, test
    >>> s1 = doctest.DocTestSuite(game)
    >>> test.testRunner.fixTestsForPy2and3(s1)
    '''
    for dtc in doctestSuite:  # Suite to DocTestCase
        if not hasattr(dtc, '_dt_test'):
            continue

        # noinspection PyProtectedMember
        dt = dtc._dt_test  # DocTest
        for example in dt.examples:
            # this probably should not go here, but we are already iterating over
            # examples
            example.want = stripAddresses(example.want, '0x...')

ADDRESS = re.compile('0x[0-9A-Fa-f]+')


def stripAddresses(textString, replacement='ADDRESS') -> str:
    '''
    Function that changes all memory addresses (pointers) in the given
    textString with (replacement).  This is useful for testing
    that a function gives an expected result even if the result
    contains references to memory locations.  So for instance:

    >>> from daseki import test
    >>> test.testRunner.stripAddresses('{0.0} <daseki.game.Game object at 0x02A87AD0>')
    '{0.0} <daseki.game.Game object at ADDRESS>'

    while this is left alone:

    >>> test.testRunner.stripAddresses('{0.0} <daseki.game.GameCollection >')
    '{0.0} <daseki.game.GameCollection >'


    For doctests, can strip to '0x...' to make it work fine with doctest.ELLIPSIS

    >>> test.testRunner.stripAddresses('{0.0} <daseki.game.Game object at 0x02A87AD0>', '0x...')
    '{0.0} <daseki.game.Game object at 0x...>'
    '''
    return ADDRESS.sub(replacement, textString)


# ------------------------------------------------------------------------------
def mainTest(*testClasses, **kwargs):
    '''
    Takes as its arguments modules (or a string 'noDocTest' or 'verbose')
    and runs all of these modules through a unittest suite

    Unless 'noDocTest' is passed as a module, a docTest
    is also performed on `__main__`, hence the name 'mainTest'.

    If 'moduleRelative' (a string) is passed as a module, then
    global variables are preserved.

    Run example (put at end of your modules):

    ::

        import unittest
        class Test(unittest.TestCase):
            def testHello(self):
                hello = 'Hello'
                self.assertEqual('Hello', hello)

        if __name__ == '__main__':
            import daseki
            daseki.mainTest(Test)


    This module tries to fix up some differences between python2 and python3 so
    that the same doctests can work.
    '''

    runAllTests = True


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

    globs = None
    if ('noDocTest' in testClasses
            or 'noDocTest' in sys.argv
            or 'nodoctest' in sys.argv
            or bool(kwargs.get('noDocTest', False))):
        skipDoctest = True
    else:
        skipDoctest = False

    # start with doc tests, then add unit tests
    if skipDoctest:
        # create a test suite for storage
        s1 = unittest.TestSuite()
    else:
        # create test suite derived from doc tests
        # here we use '__main__' instead of a module
        if ('moduleRelative' in testClasses or
                'moduleRelative' in sys.argv or
                bool(kwargs.get('moduleRelative', False))):
            pass
        else:
            for di in defaultImports:
                globs = __import__(di).__dict__.copy()
        try:
            s1 = doctest.DocTestSuite(
                                      '__main__',
                                      globs=globs,
                                      optionflags=optionflags,
                                      )
        except ValueError:  # no docstrings
            s1 = unittest.TestSuite()

    verbosity = 1
    if 'verbose' in testClasses or 'verbose' in sys.argv or bool(kwargs.get('verbose', False)):
        verbosity = 2  # this seems to hide most display

    displayNames = False
    if ('list' in sys.argv or
            'display' in sys.argv or
            bool(kwargs.get('display', False)) or
            bool(kwargs.get('list', False))):
        displayNames = True
        runAllTests = False

    runThisTest = None
    if len(sys.argv) == 2:
        arg = sys.argv[1].lower()
        if arg not in ['list', 'display', 'verbose', 'nodoctest']:
            # run a test directly named in this module
            runThisTest = sys.argv[1]
    if bool(kwargs.get('runTest', False)):
        runThisTest = kwargs.get('runTest', False)

    # -f, --failfast
    if ('onlyDocTest' in sys.argv or
            'onlyDocTest' in testClasses or
            bool(kwargs.get('onlyDocTest', False))):
        testClasses = []  # remove cases
    for t in testClasses:
        if not isinstance(t, str):
            if displayNames is True:
                for tName in unittest.defaultTestLoader.getTestCaseNames(t):
                    print('Unit Test Method: %s' % tName)
            if runThisTest is not None:
                tObj = t()  # call class
                # search all names for case-insensitive match
                for name in dir(tObj):
                    if (name.lower() == runThisTest.lower()
                            or name.lower() == ('test' + runThisTest.lower())
                            or name.lower() == ('xtest' + runThisTest.lower())):
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

    # Add _DOC_ATTR tests...
    if not skipDoctest:
        stacks = inspect.stack()
        if len(stacks) > 1:
            outerFrameTuple = stacks[1]
        else:
            outerFrameTuple = stacks[0]
        outerFrame = outerFrameTuple[0]
        outerFilename = outerFrameTuple[1]
        localVariables = list(outerFrame.f_locals.values())
        addDocAttrTestsToSuite(s1, localVariables, outerFilename, globs, optionflags)

    if runAllTests is True:
        fixTestsForPy2and3(s1)

        runner = unittest.TextTestRunner()
        runner.verbosity = verbosity
        _unused_testResult = runner.run(s1)

if __name__ == '__main__':
    mainTest()

