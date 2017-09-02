#!/usr/bin/env python
# -*- coding: utf-8 -*-
# prodotti.py


import shutil

from tools import readDate, unitConversion, ProductException, color


data = {}
areas = {'prosecco': 6.9568, 'pinot': 0.9946,}


class validate ():
    
    def name (string):
        names = []
        for product in list(data):
            if product.count(string.lower()) == 1:
                names.append(product)
        if not names:
            raise ProductException(
                "No product or similar products called \"%s\" found in the "
                "database." % (string))
        return names

    def unit (string, product):
        unit = None
        if string.lower() != data[product.lower()]['unit']:
            raise ProductException(
                "The measuring unit specified (%s) is not valid for the "
                "product %s." % (string.lower(), product.upper()))
        else:
            unit = string.lower()
        return unit
    
    def pos (string):
        pos = []
        if not string:
            pos = list(areas)
        else:
            for entry in [x.lower() for x in string.split(',')]:
                if not entry in areas:
                    raise ProductException(
                        "The usage area specified (%s) was not found among "
                        "the list of available areas: %s" % (
                        entry.capitalize(),
                        ' '.join([x.capitalize() for x in areas])))
                else:
                    pos.append(entry)
        return pos


def getData():
    return data


def read (file='prodotti.txt'):
    try:
        with open(file, encoding='utf-8') as fp:
            raw = fp.read().splitlines()
    except FileNotFoundError:
        #FIX: Something's wrong, check please
        raw = ''
    for line in raw:
        if len(line) > 1:
            if line[0:4] != "    ":
                name = line.lower()
                data[name] = {}
            elif line[0:4] == "    ":
                key = line[4:].split(':')[0]
                value = ':'.join(line[4:].split(':')[1:]).lstrip()
                data[name][key] = value
    for product in list(data):
            data[product]['unit'] = data[product]['min-max'].split(' ')[1][:-3]
            minmax = data[product]['min-max'].split(' ')[0]
            if len(minmax.split('-')) > 1:
                data[product]['minmax'] = [float(x) for x in minmax.split('-')]
            else:
                data[product]['minmax'] = [float(minmax), float(minmax)]
            del data[product]['min-max']
            data[product]['carenza'] = int(data[product]['carenza'][:-2])
            data[product]['num'] = int(data[product]['num'])
            data[product]['obiettivo'] = data[product]['obiettivo'].split(',')


















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
    for prodotto in list(data):
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


def show (mode='complete'):
    if mode == 'short':
        print("NOME%s  MIN-MAX   /ha  CARENZA  N  OBIETTIVO" % (' '*16))
    elif mode == 'complete':
        print("")
    for entry in sorted(list(data)):
        if mode == 'complete':
            if int(data[entry]['num']):
                num = "\n    trattamenti max: %s" % data[entry]['num']
            else:
                num = ""
            min, max = data[entry]['minmax']
            if float(min) == float(max):
                minmax = "%.2f" % (float(max))
            else:
                minmax = "%.2f-%.2f" % (float(min), float(max))
            print("%s%s%s\n    min-max: %s %s/ha\n    carenza: %sgg%s\n    obiettivo: %s\n    note: %s%s%s" % (
                color.CYAN, entry.upper(), color.END,
                minmax, data[entry]['unit'],
                data[entry]['carenza'], num,
                data[entry]['obiettivo'],
                color.GRAY, alignText(data[entry]['note'], 10), color.END
            ))
        elif mode == 'short':
            if int(data[entry]['num']):
                num = " %s" % str(data[entry]['num']).rjust(2)
            else:
                num = "  /"
            columns, rows = shutil.get_terminal_size()
            if len(data[entry]['obiettivo']) > (columns - 48):
                obiettivo = data[entry]['obiettivo'][:columns - 48 - 4] + "..."
            else:
                obiettivo = ','.join(data[entry]['obiettivo'])
            print("%s%s%s%.2f-%.2f %s/ha %sgg%s %s" % (
                color.CYAN, entry.upper().ljust(20), color.END, 
                float(data[entry]['minmax'][0]), float(data[entry]['minmax'][1]),
                data[entry]['unit'].rjust(2),
                str(data[entry]['carenza']).rjust(6), num,
                obiettivo,
            ))
