'''
All files need to be able to import this file, so do not put any imports here.
'''

class DasekiException(Exception):
    pass

class RetrosheetException(DasekiException):
    pass

class GameParseException(DasekiException):
    pass