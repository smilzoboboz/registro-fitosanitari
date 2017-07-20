#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import re
import shutil
import datetime

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


databaseProdotti = {}
tolerance = 0.05  # tolerance on min-max dosage (5%)
superfici = {'prosecco': 6.9540, 'pinot': 0.9946,}
defaultPos = list(superfici)  # product usage areas; default = all areas
lineaRegistro = re.compile('([0-9][0-9][0-9][0-9]\/[0-9][0-9]\/[0-9][0-9]) (.*) (-*[.0-9]+)[ ]*([mMkK]*[lLgG])[ ]*[-<]*([^ ]*)[ ]*[#]*[ ]*(.*)')


class register:

    def add (line, metodo):
        # usage example:
        #   program acquisto 2017/07/15 Grifon Più 80 WG 10 kg
        #   program acquisto Grifon 10 Kg
        # check if the date was omitted, if that's the case, use today's date
        try:
            int(line[0:4])
        except ValueError:
            line = datetime.date.today().strftime('%Y/%m/%d ') + line
        # match the string and find key values
        prog = lineaRegistro
        result = prog.match(line)
        date = result.group(1)
        name = result.group(2).lower()
        unit, qty = unitConversion(result.group(4).lower(), result.group(3))
        if metodo == 'utilizzo' and qty > 0:
            #TODO: Check min/max usage scenarios and warn if overdue
            qty = qty * (-1)
        # product usage position and notes
        pos = ''
        if qty < 0:
            if result.group(5):
                pos = " <-%s" % result.group(5)
        note = ''
        if result.group(6):
            note = ' # %s' % result.group(6)
        # product name check upon the database
        if not name.lower() in list(databaseProdotti):
            print(
                "\nIl prodotto indicato (%s) non è presente nel database." % (
                name.capitalize()))
            similar = []
            counter = 1
            for product in list(databaseProdotti):
                if product.count(name) == 1:
                    similar.append(product)
            if len(similar) > 0:
                print(
                    "Il programma ha trovato in database i seguenti prodotti "
                    "simili a quello indicato:")
                for item in similar:
                    print("    %d. %s" % (counter, item.capitalize()))
                    counter += 1
                sys.stdout.write(
                    "Inserire il numero corrispondente al prodotto per "
                    "utilizzarlo al posto di quello indicato (0 per "
                    "annullare): ")
                answer = input()
                if int(answer) == 0:
                    raise ProductException("L'utente ha annullato l'inserimento.")
                name = similar[int(answer) - 1]
            else:
                print(
                    "Completare il database col prodotto mancante prima di "
                    "continuare con l'inserimento dei dati.")
                raise ProductException()
        #TODO: Check unit on products database for conformity (liquid/solid)
        # write to file and show the result
        with open('registro.txt', 'a', encoding='utf-8') as fp:
            fp.write(
                "%s %s %.2f %s%s%s\n" % (
                date, name, qty, unit, pos, note))
        print(
            "\n%s %s %.2f %s%s%s" % (
            date, name.capitalize(), qty, unit, pos, note)) 

    def read (mode='reg', search=None, file='registro.txt'):
        databaseTemporaneo = {}
        registroTemporaneo = {}
        counter = 0
        with open(file, encoding='utf-8') as fp:
            raw = fp.read().splitlines()
        for line in raw:
            prog = lineaRegistro
            result = prog.match(line)
            date = result.group(1)
            name = result.group(2).lower()
            unit, qty = unitConversion(result.group(4).lower(), result.group(3))
            if qty < 0:
                if result.group(5):
                    pos = result.group(5).lower().split(',')
                else:
                    pos = defaultPos
            else:
                pos = []
            if result.group(6):
                note = '# %s' % result.group(6)
            else:
                note = ''
            registroTemporaneo[counter] = {
                'date': date,
                'name': name.lower(),
                'qty': qty,
                'unit': unit,
                'pos': pos,
                'note': note}
            counter += 1
        awfulList = [[x, registroTemporaneo[x]['date']] for x in list(registroTemporaneo)]
        #TODO Add reverse sorting
        awfulList.sort(key=getKey)
        smartDate = ""
        carenza = 0
        checkDatePrint = False
        for index in [ x[0] for x in awfulList]:
            name = registroTemporaneo[index]['name']
            date = registroTemporaneo[index]['date']
            qty = registroTemporaneo[index]['qty']
            unit = registroTemporaneo[index]['unit']
            pos = registroTemporaneo[index]['pos']
            note = registroTemporaneo[index]['note']
            if name not in list(databaseTemporaneo):
                databaseTemporaneo[name] = {'qty': qty, 'unit': unit, 'num': 0}
            else:
                databaseTemporaneo[name]['qty'] += qty
            if date == smartDate and checkDatePrint:
                smartDate = "          "
            else:
                checkDatePrint = False
                smartDate = "\n%s" % date
            if mode == 'reg':
                if qty < 0:
                    colorModA = color.RED
                else:
                    colorModA = ''
                if not search:
                    print("%s %s%s%s %s%6.2f%s %s | %5.2f %s  %s%s%s" % (
                        smartDate,
                        color.CYAN, name.upper().rjust(18), color.END,
                        colorModA, qty, color.END, unit.ljust(2),
                        float(databaseTemporaneo[name]['qty']), unit.ljust(2),
                        color.GRAY, note, color.END
                    ))
                    checkDatePrint = True
                elif sum([[x.lower() for x in registroTemporaneo[index]['pos']].count(y) for y in search]):
                    today = datetime.datetime.strptime(datetime.datetime.today().strftime('%Y/%m/%d'), '%Y/%m/%d')
                    days = (today - datetime.datetime.strptime(date, '%Y/%m/%d')).days
                    if carenza < int(databaseProdotti[name]['carenza']) - days:
                        carenza = int(databaseProdotti[name]['carenza']) - days
                    databaseTemporaneo[name]['num'] += 1
                    qty = -qty
                    if int(databaseProdotti[name]['num']):
                        numMax = '/%s' % str(databaseProdotti[name]['num']).ljust(2)
                    else:
                        numMax = '/- '
                    area = sum([superfici[x.lower()] for x in registroTemporaneo[index]['pos']])
                    if (
                        (qty/area) > float(databaseProdotti[name]['minmax'][1])*(1+tolerance) or
                        (qty/area) < float(databaseProdotti[name]['minmax'][0])*(1-tolerance)):
                        qtyHa = "%s%.2f%s %s/ha (%.2f-%.2f %s/ha)" % (
                            color.RED, qty/area, color.END,
                            databaseProdotti[name]['unit'],
                            float(databaseProdotti[name]['minmax'][0]),
                            float(databaseProdotti[name]['minmax'][1]),
                            databaseProdotti[name]['unit'])
                    elif (
                        (qty/area) > float(databaseProdotti[name]['minmax'][1]) or
                        (qty/area) < float(databaseProdotti[name]['minmax'][0])):
                        qtyHa = "%.2f %s/ha (%.2f-%.2f %s/ha)" % (
                            qty/area, databaseProdotti[name]['unit'],
                            float(databaseProdotti[name]['minmax'][0]),
                            float(databaseProdotti[name]['minmax'][1]),
                            databaseProdotti[name]['unit'])
                    else:
                        qtyHa = "%.2f %s" % (
                            qty/area, databaseProdotti[name]['unit'])
                    print("%s %s%s%s %6.2f %s | %d%s %s" % (
                        smartDate,
                        color.CYAN, name.upper().rjust(18), color.END,
                        qty, unit.ljust(2),
                        databaseTemporaneo[name]['num'], numMax, qtyHa)
                    )
                    checkDatePrint = True
            if checkDatePrint:
                smartDate = date
        if not search:
            if mode == 'reg':
                print("\n%s" % ('-'*10))
            for product in sorted(list(databaseTemporaneo)):
                if (
                    float(databaseTemporaneo[product]['qty']) > 0.001 or
                    float(databaseTemporaneo[product]['qty']) < (-0.001)):
                    print("%s%s%s %5.2f %s" % (
                        color.CYAN, product.ljust(18).upper(), color.END,
                        databaseTemporaneo[product]['qty'],
                        databaseTemporaneo[product]['unit']
                    ))
        else:
            print('-'*10)
            print("Carenza corrente: %d" % carenza)


class database:

    def write (line, file='prodotti.txt'):
        # usage example:
        #   tiolene 200-300 ml/ha 20gg 0 peronospora various uninteresting notes
        #   grifon 0.4 0.5 kg 5
        prog = re.compile('(.*) ([-.0-9]+) ([mMlLkKgG]+)[ha/]* ([0-9]+)[gG]* ([0-9]*) *([^#]*)#*(.*)')
        result = prog.match(line)
        name = result.group(1)
        if len(result.group(2).split('-')) > 1:
            min, max = result.group(2).split('-')
        else:
            min, max = result.group(2), result.group(2)
        unit = result.group(3).lower()
        carenza = int(result.group(4))
        num = int(result.group(5))
        obj = result.group(6).rstrip(" ")
        note = result.group(7)
        cUnit, min = unitConversion(unit, min)
        cUnit, max = unitConversion(unit, max)
        similar = []
        if min != max:
            minmax = "%.2f-%.2f" % (min, max)
        elif min == max:
            minmax = "%.2f" % min
        for prodotto in list(databaseProdotti):
            if prodotto.count(name.lower()) == 1:
                similar.append(prodotto)
        if len(similar) > 0:
            print("Sono stati trovati alcuni prodotti simili a quello proposto:")
            for prodotto in similar:
                print("  %s" % prodotto.capitalize())
            answer = query_yes_no("\nSi è sicuri di continuare con l'aggiunta di un nuovo prodotto?", 'no')
            if answer is False:
                raise ProductException()
        with open(file, 'a', encoding='utf-8') as fp:
            fp.write("\n%s\n    min-max: %s %s/ha\n    carenza: %dgg\n    num: %d\n    obiettivo: %s\n    note: %s\n" % (
                name, minmax, cUnit, carenza, num, obj, note))
        print("\n%s\n    min-max: %s %s/ha\n    carenza: %dgg\n    num: %d\n    obiettivo: %s\n    note: %s%s%s" % (
            name, minmax, cUnit, carenza, num, obj, color.GRAY, alignText(note, 10), color.END))
        print("%sProdotto aggiunto correttamente%s" % (color.GREEN, color.END))

    def read (file='prodotti.txt'):
        try:
            with open(file, encoding='utf-8') as fp:
                raw = fp.read().splitlines()
        except FileNotFoundError:
            raw = ''
        for line in raw:
            if len(line) > 1:
                if line[0:4] != "    ":
                    name = line.lower()
                    databaseProdotti[name] = {}
                elif line[0:4] == "    ":
                    key = line[4:].split(':')[0]
                    value = ':'.join(line[4:].split(':')[1:]).lstrip()
                    databaseProdotti[name][key] = value
        for product in list(databaseProdotti):
                databaseProdotti[product]['unit'] = databaseProdotti[product]['min-max'].split(' ')[1][:-3]
                minmax = databaseProdotti[product]['min-max'].split(' ')[0]
                if len(minmax.split('-')) > 1:
                    databaseProdotti[product]['minmax'] = minmax.split('-')
                else:
                    databaseProdotti[product]['minmax'] = [minmax, minmax]
                del databaseProdotti[product]['min-max']
                databaseProdotti[product]['carenza'] = databaseProdotti[product]['carenza'][:-2]

    def show (mode='complete'):
        if mode == 'short':
            print("NOME%s  MIN-MAX   /ha  CARENZA  N  OBIETTIVO" % (' '*16))
        elif mode == 'complete':
            print("")
        for entry in sorted(list(databaseProdotti)):
            if mode == 'complete':
                if int(databaseProdotti[entry]['num']):
                    num = "\n    trattamenti max: %s" % databaseProdotti[entry]['num']
                else:
                    num = ""
                min, max = databaseProdotti[entry]['minmax']
                if float(min) == float(max):
                    minmax = "%.2f" % (float(max))
                else:
                    minmax = "%.2f-%.2f" % (float(min), float(max))
                print("%s%s%s\n    min-max: %s %s/ha\n    carenza: %sgg%s\n    obiettivo: %s\n    note: %s%s%s" % (
                    color.CYAN, entry.upper(), color.END,
                    minmax, databaseProdotti[entry]['unit'],
                    databaseProdotti[entry]['carenza'], num,
                    databaseProdotti[entry]['obiettivo'],
                    color.GRAY, alignText(databaseProdotti[entry]['note'], 10), color.END
                ))
            elif mode == 'short':
                if int(databaseProdotti[entry]['num']):
                    num = " %s" % str(databaseProdotti[entry]['num']).rjust(2)
                else:
                    num = "  /"
                columns, rows = shutil.get_terminal_size()
                if len(databaseProdotti[entry]['obiettivo']) > (columns - 48):
                    obiettivo = databaseProdotti[entry]['obiettivo'][:columns - 48 - 4] + "..."
                else:
                    obiettivo = databaseProdotti[entry]['obiettivo']
                print("%s%s%s%.2f-%.2f %s/ha %sgg%s %s" % (
                    color.CYAN, entry.upper().ljust(20), color.END, 
                    float(databaseProdotti[entry]['minmax'][0]), float(databaseProdotti[entry]['minmax'][1]),
                    databaseProdotti[entry]['unit'].rjust(2),
                    databaseProdotti[entry]['carenza'].rjust(6), num,
                    obiettivo,
                ))

def cliHandler (args):
    helpArguments = ['help', 'aiuto']
    if len(args) <= 1:
        print("HELP")
    elif len(args) > 1:
        if args[1].lower() in ['add', 'agg', 'acquisto', 'aggiungi', 'aggiunta']:
            if len(args) == 2 or args[2].lower() in helpArguments:
                print("add HELP")
            else:
                register.add(' '.join(args[2:]), 'acquisto')
        elif args[1].lower() in ['use', 'uso', 'utilizzo', 'consumo']:
            if len(args) == 2 or args[2].lower() in helpArguments:
                print("use HELP")
            else:
                register.add(' '.join(args[2:]), 'utilizzo')
        elif args[1].lower() in ['bilancio', 'bal', 'bil']:
            register.read('bal')
        elif args[1].lower() in ['reg', 'registro']:
            if len(args) > 2:
                register.read('reg', args[2:])
            else:
                register.read('reg')
        elif args[1].lower() in ['prodotti']:
            if len(args) == 3 and args[2].lower() in helpArguments:
                print("prodotti HELP")
            elif len(args) > 2:
                if args[2] in ['corto', 'compatto']:
                    database.show('short')
                else:
                    print("specific balances")
            else:
                database.show()
        elif args[1].lower() in ['prodotto']:
            if len(args) == 3 and args[2].lower() in helpArguments:
                print("inserimento HELP")
            else:
                database.write(' '.join(args[2:]))
                

database.read()
cliHandler(sys.argv)
#TODO bal and reg