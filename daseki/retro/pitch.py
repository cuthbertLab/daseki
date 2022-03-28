# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Name:         pitch.py
# Purpose:      a single pitch event in a retrosheet eventfile event
#
# Authors:      Michael Scott Cuthbert
#
# Copyright:    Copyright © 2015 Michael Scott Cuthbert / cuthbertLab
# License:      BSD, see license.txt
# -----------------------------------------------------------------------------
class Pitch(object):
    '''
    A single Pitch in a game.  Not used yet.
    '''
    pitchEvents = {'+': 'following pickoff throw by catcher',
                   '*': 'following pitch was blocked by catcher',
                   '.': 'play not involving the batter',
                   '1': 'pickoff throw to first',
                   '2': 'pickoff throw to second',
                   '3': 'pickoff throw to third',
                   '>': 'runner going on the pitch',
                   'B': 'ball',
                   'C': 'called strike',
                   'F': 'foul',
                   'H': 'hit batter',
                   'I': 'intentional ball',
                   'K': 'strike (unknown type)',
                   'L': 'foul bunt',
                   'M': 'missed bunt attempt',
                   'N': 'no pitch (balks and interference)',
                   'O': 'foul tip on bunt',
                   'P': 'pitchout',
                   'Q': 'swinging on pitchout',
                   'S': 'swinging strike',
                   'T': 'foul tip',
                   'U': 'unknown or missed pitch',
                   'V': 'called ball because pitcher went to mouth',
                   'X': 'ball put into play by batter',
                   'Y': 'ball put into play on pitchout'
                   }
