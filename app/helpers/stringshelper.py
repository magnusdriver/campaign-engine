import re

def getIdFromString(string):
    numberPattern = re.compile(r'\d+')

    return numberPattern.search(string)