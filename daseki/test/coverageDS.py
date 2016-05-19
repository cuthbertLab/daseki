# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         coverageM21.py
# Purpose:      Starts Coverage w/ default arguments
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2014-15 Michael Scott Cuthbert and the music21 Project
# License:      LGPL or BSD, see license.txt
#-------------------------------------------------------------------------------

omit_modules = [
                'daseki/ext/*',
                ]
exclude_lines = [
                r'\s*import daseki\s*',
                r'\s*daseki.mainTest\(\)\s*',
                ]

def getCoverage():    
    try:
        import coverage
        cov = coverage.coverage(omit=omit_modules)
        for e in exclude_lines:
            cov.exclude(e, which='exclude')
        cov.start()
    except ImportError:
        cov = None
    return cov

def stopCoverage(cov):
    if cov is not None:
        cov.stop()
        cov.save()
