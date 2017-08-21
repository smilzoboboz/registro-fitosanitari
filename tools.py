#!/usr/bin/env python
# prodotti.py


import sys
import datetime
import os

if os.name is not "posix":
    import colorama
    colorama.init()

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   GRAY = '\033[90m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

class ProductException(Exception):
    pass


def readDate (string):
    """ Read multiple-formats string date as a datetime object
    
    Valid date formats are "YYYY/MM/DD", "DD/MM/YYYY" and "DD/MM" (the current
    year will be used if the year is omitted).
    
    NOTE: The "MM/DD" format will only be recognized if the day is further 
          than 12
    """
    format = None
    splits = string.split('/')
    # Format "%d/%m", current year will be automatically added
    if len(splits) == 2:
        # Fast check for mistaken months for days. Won't work if day is 
        # between 1 and 12 but that can't be fixed
        if int(splits[1]) > 12:
            splits = [splits[1], splits[0]]
        string = str(datetime.datetime.today().year) + '/' + '/'.join(["%02d" % int(x) for x in splits])
        format = "%Y/%d/%m"
    # Formats including the year, either leading or trailing
    elif len(splits) == 3:
        if int(splits[0]) > 31:
            format = "%Y/%m/%d"
        elif int(splits[2]) > 31:
            format = "%d/%m/%Y"
    # If none of the above recognized anything raise and exception
    if not format:
        raise ProductException("Formato data non corretto.")
    # Return date in a datetime.date format
    return datetime.datetime.strptime(string, format)


def alignText (text, offset):
    """ Text alignment up to 80 columns for longer notes
    
    "offset" equals to leading characters to fill as blank (except for the
    very first line) to keep the text left aligned.
    """
    columns, rows = shutil.get_terminal_size()
    textVar = ''
    max = int(columns) - int(offset)
    # Arbitrary max lenght setting to 80
    if max > 80:
        max = 80
    if len(text) < max:
        return "%s\n" % text
    while len(text) > max:
        counter = max-1
        while counter != 0:
            if text[counter] == ' ':
                break
            counter -= 1
        if not textVar:
            textVar += "%s\n" % text[:counter+1]
        else:
            textVar += "%s%s\n" % (' '*offset, text[:counter+1])
        text = text[counter+1:]
    textVar += "%s%s\n" % (' '*offset, text)
    return textVar


def query_yes_no(question, default="si"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"si": True, "s": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [s/n] "
    elif default == "si":
        prompt = " [S/n] "
    elif default == "no":
        prompt = " [s/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)
    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Rispondere 'si' o 'no' "
                             "(oppure 's' o 'n').\n")


def getKey(item):
    return item[1]


def unitConversion (unit, qty):
    # TODO: full coverage
    # target units are liters and kilograms
    # liquids section
    multiplier = 1
    unit = unit.lower()
    if unit =='ml':
        multiplier = 0.001
    if unit.count('l'):
        return ('l', float(qty) * multiplier)
    # solids section
    multiplier = 0.001
    if unit == 'kg':
        multiplier = 1
    if unit.count('g'):
        return ('kg', float(qty) * multiplier)
    raise ValueError
