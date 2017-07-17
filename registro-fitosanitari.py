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
    columns, rows = shutil.get_terminal_size()
    textVar = ''
    max = int(columns) - int(offset)
    if max > 80:
        max = 80
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


databaseProdotti = {}
databaseCorrente = ""  # Future ledger-like dat file
defaultPos = ['prosecco', 'pinot']
lineaRegistro = re.compile('([0-9][0-9][0-9][0-9]\/[0-9][0-9]\/[0-9][0-9]) (.*) (-*[.0-9]+)[ ]*([mMkK]*[lLgG])[ ]*[-<]*([^ ]*)[ ]*[#]*[ ]*(.*)')

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

def prodotto (name, unit, min, max, carenza, comp=[], notes=''):
    # check for duplicate entries
    for item in list(databaseProdotti):
        if item == name.lower():
            answer = query_yes_no("Prodotto già inserito nel database, sostituire i valori esistenti con quelli proposti?", 'no')
            if answer is False:
                raise ProductException("Prodotto duplicato, ignorato.")
    # check for valid input values
    if not str(unit).lower() in ['g', 'kg', 'l', 'ml']:
        raise ProductException("Errore nelle unità di misura.")
    if not type(min) in [float, int] and type(max) in [float, int]:
        raise ProductException("Valore per hl non numerico.")
    cUnit, min = unitConversion(unit, min)
    cUnit, max = unitConversion(unit, max)
    if not type(carenza) == int:
        raise ProductException("Carenza non espressa con un numero intero.")
    # database entry compilation
    databaseProdotti[name.lower()] = {
        'unit': cUnit,
        'minmax': [min, max],
        'carenza': carenza,
        'comp': comp,
        'notes': notes
        }

def acquisto (date, name, unit, qty):
    if not name.lower() in list(databaseProdotti):
        raise ProductException("Il prodotto \"%s\" non esiste attualmente nel database, prima di procedere aggiungerlo." % name)
    cUnit, qty = unitConversion(unit, qty)
    global databaseCorrente
    databaseCorrente += "%s %s %.2f %s\n" % (date, name.capitalize(), qty, cUnit)

def methodAggiunta (line, metodo):
    # usage example:
    #   program acquisto 2017/07/15 Grifon Più 80 WG 10 kg
    #   program acquisto Grifon 10 Kg
    methodReadDatabase()
    try: int(line[0:4])
    except ValueError: line = datetime.date.today().strftime('%Y/%m/%d ') + line
    prog = lineaRegistro
    result = prog.match(line)
    date = result.group(1)
    name = result.group(2).lower()
    unit, qty = unitConversion(result.group(4).lower(), result.group(3))
    if metodo == 'utilizzo':
        #TODO: Check min/max usage scenarios and warn if overdue
        qty = qty * (-1)
    pos = ''
    if qty < 0:
        if result.group(5):
            pos = " <-%s" % result.group(5)
    note = ''
    if result.group(6):
        note = ' # %s' % result.group(6)
    if not name.lower() in list(databaseProdotti):
        print("\nIl prodotto indicato (%s) non è presente nel database." % (name.capitalize()))
        similar = []
        counter = 1
        for product in list(databaseProdotti):
            if product.count(name) == 1:
                similar.append(product)
        if len(similar) > 0:
            print("Il programma ha trovato in database i seguenti prodotti simili a quello indicato:")
            for item in similar:
                print("    %d. %s" % (counter, item.capitalize()))
                counter += 1
            sys.stdout.write("Inserire il numero corrispondente al prodotto per utilizzarlo al posto di quello indicato (0 per annullare): ")
            answer = input()
            if int(answer) == 0:
                raise ProductException("L'utente ha annullato l'inserimento.")
            name = similar[int(answer) - 1]
        else:
            print("Completare il database col prodotto mancante prima di continuare con l'inserimento dei dati.")
            raise ProductException()
    #TODO: Check unit on products database for conformity (liquid/solid)
    with open('registro.txt', 'a', encoding='utf-8') as fp:
        fp.write("%s %s %.2f %s%s%s\n" % (date, name, qty, unit, pos, note))
    print("\n%s %s %.2f %s%s%s" % (date, name.capitalize(), qty, unit, pos, note)) 

def methodReadLog (mode='reg', file='registro.txt'):
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
                pos = ['prosecco', 'pinot']
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
    for index in [ x[0] for x in awfulList]:
        name = registroTemporaneo[index]['name']
        date = registroTemporaneo[index]['date']
        qty = registroTemporaneo[index]['qty']
        unit = registroTemporaneo[index]['unit']
        pos = registroTemporaneo[index]['pos']
        note = registroTemporaneo[index]['note']
        if name not in list(databaseTemporaneo):
            databaseTemporaneo[name] = {'qty': qty, 'unit': unit}
        else:
            databaseTemporaneo[name]['qty'] += qty
        if mode == 'reg':
            if qty < 0:
                colorModA = color.RED
            else:
                colorModA = ''
            print("%s %s%s%s %s%6.2f%s %s | %5.2f %s  %s%s%s" % (
                date,
                color.CYAN, name.capitalize().rjust(15), color.END,
                colorModA, qty, color.END, unit.ljust(2),
                float(databaseTemporaneo[name]['qty']), unit.ljust(2),
                color.GRAY, note, color.END
            ))
    if mode == 'reg':
        print('-'*10)
    for product in list(databaseTemporaneo):
        print("%s%s%s %5.2f %s" % (
            color.CYAN, product.ljust(15).capitalize(), color.END,
            databaseTemporaneo[product]['qty'], databaseTemporaneo[product]['unit']
        ))
        

def methodWriteDatabase (line, file='prodotti.txt'):
    # usage example:
    #   tiolene 200-300 ml/ha 20gg various uninteresting notes
    #   grifon 0.4 0.5 kg 5
    prog = re.compile('(.*) ([-.0-9]+) ([mMlLkKgG]+)[hl/]* ([0-9]+)[gG]* (.*)')
    result = prog.match(line)
    name = result.group(1)
    min, max = result.group(2).split('-')
    unit = result.group(3).lower()
    carenza = int(result.group(4))
    note = result.group(5)
    cUnit, min = unitConversion(unit, min)
    cUnit, max = unitConversion(unit, max)
    similar = []
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
        fp.write("\n%s\n    min-max: %.2f-%.2f %s/ha\n    carenza: %dgg\n    note: %s\n" % (
            name, min, max, cUnit, carenza, note))
    print("Prodotto aggiunto correttamente:")
    print("\n%s\n    min-max: %.2f-%.2f %s/ha\n    carenza: %dgg\n    note: %s%s%s" % (
        name, min, max, cUnit, carenza, color.GRAY, alignText(note, 10), color.END))

def methodReadDatabase (file='prodotti.txt'):
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
            databaseProdotti[product]['minmax'] = databaseProdotti[product]['min-max'].split(' ')[0].split('-')
            del databaseProdotti[product]['min-max']
            databaseProdotti[product]['carenza'] = databaseProdotti[product]['carenza'][:-2]

def methodPrintDatabase (mode='corto'):
    if len(list(databaseProdotti)) == 0:
        methodReadDatabase()
    if mode == 'corto':
        print("NOME%s  MIN-MAX   /ha  CARENZA" % (' '*16))
    elif mode == 'completo':
        print("")
    for entry in list(databaseProdotti):
        if mode == 'completo':
            print("%s%s%s\n    min-max: %.2f-%.2f %s/ha\n    carenza: %sgg\n    note: %s%s%s" % (
                color.CYAN, entry.upper(), color.END,
                float(databaseProdotti[entry]['minmax'][0]), float(databaseProdotti[entry]['minmax'][1]),
                databaseProdotti[entry]['unit'],
                databaseProdotti[entry]['carenza'],
                color.GRAY, alignText(databaseProdotti[entry]['note'], 10), color.END
            ))
        elif mode == 'corto':
            print("%s%s%s%.2f-%.2f %s/ha %sgg" % (
                color.CYAN, entry.capitalize().ljust(20), color.END, 
                float(databaseProdotti[entry]['minmax'][0]), float(databaseProdotti[entry]['minmax'][1]),
                databaseProdotti[entry]['unit'].rjust(2),
                databaseProdotti[entry]['carenza'].rjust(6)
            ))

def cliHandler (args):
    helpArguments = ['help', 'aiuto']
    if len(args) == 0:
        print("HELP")
    elif len(args) > 0:
        if args[0].lower() in ['add', 'acquisto', 'aggiungi', 'aggiunta']:
            if len(args) == 1 or args[1].lower() in helpArguments:
                print("add HELP")
            else:
                methodAggiunta(' '.join(args[1:]), 'acquisto')
        elif args[0].lower() in ['use', 'uso', 'utilizzo', 'consumo']:
            if len(args) == 1 or args[1].lower() in helpArguments:
                print("use HELP")
            else:
                methodAggiunta(' '.join(args[1:]), 'utilizzo')
            

methodReadDatabase()
if sys.argv[1].lower() == 'acquisto':
    methodAggiunta(' '.join(sys.argv[2:]), 'acquisto')
elif sys.argv[1].lower() == 'utilizzo':
    methodAggiunta(' '.join(sys.argv[2:]), 'utilizzo')
elif sys.argv[1].lower() == 'prodotto':
    methodWriteDatabase(' '.join(sys.argv[2:]))
elif sys.argv[1].lower() == 'prodotti':
    methodPrintDatabase(sys.argv[2])
elif sys.argv[1].lower() in ['bal', 'reg']:
    methodReadLog(sys.argv[1])
#TODO bal and reg
