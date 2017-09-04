#!/usr/bin/env python
# -*- coding: utf-8 -*-
# prodotti.py


import re
import datetime
import products
from tools import readDate, unitConversion, ProductException, color, query_yes_no, getKey


data = {}
trattamento = {}
lineaRegistro = re.compile('([0-9/]*) (.*) (-*[^a-zA-Z#]+)[ ]*([mMkK]*[lLgG])[ ]*[-<]*([^# ]*)[ ]*[#]*[ ]*(.*)')

def add (line, metodo='add', quiet=False, preview=True):
    """ Add entries to the registry
    
    Changes can be either product acquisition or usage. Usage takes the area of
    use optional argument.
    
    Examples:
        add('20/05 grifon 20 kg', quiet=True)
        add('Shelter 3.5 l prosecco #serious note', 'use')
    """
    productLine = {}
    # check if the date was omitted, if that's the case, use today's date
    try:
        int(line.split(' ')[0].split('/')[0])
    except ValueError:
        line = datetime.date.today().strftime('%Y/%m/%d ') + line
    # match the string and find key values
    prog = lineaRegistro
    result = prog.match(line)
    productLine['date'] = readDate(result.group(1))
    unit, qty = unitConversion(result.group(4).lower(), eval(result.group(3)))
    if metodo == 'use' and qty >= 0:
        qty = qty * (-1)
    productLine['qty'] = qty
    if qty <= 0:
            productLine['pos'] = products.validate.pos(result.group(5))
    if result.group(6):
        productLine['notes'] = result.group(6)
    # product name check upon the database
    similar = products.validate.name(result.group(2).lower())
    if len(similar) == 1:
        productLine['name'] = similar[0]
    elif len(similar) > 1:
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
        productLine['name'] = similar[int(answer) - 1]
    else:
        print(
            "Completare il database col prodotto mancante prima di "
            "continuare con l'inserimento dei dati.")
        raise ProductException()
    productLine['unit'] = products.validate.unit(unit, productLine['name'])
    if preview:
        noffset = 1
        qoffset = productLine['qty']
    else:
        noffset = 0
        qoffset = 0
    # On-screen print
    show(productLine, tnum=noffset, tleft=qoffset)
    # Format optional arguments for register witing
    if 'pos' in list(productLine):
        if len(productLine['pos']) == len(list(products.areas)):
            warea = ""
        else:
            warea = " <-%s" % ','.join(productLine['pos'])
    else:
        warea = ""
    if 'notes' in list(productLine):
        wnote = " # %s" % productLine['notes']
    else:
        wnote = ""
    print("")
    # Ask whether or not to proceed writing to disk
    if not quiet:
        answer = query_yes_no("Procedere con la scrittura su file?")
        if not answer:
            return
    # Write changes to disk
    with open('registro.txt', 'a', encoding='utf-8') as fp:
        fp.write("%s %s %.2f %s%s%s\n" % (
            productLine['date'].strftime("%Y/%m/%d"), productLine['name'],
            productLine['qty'], productLine['unit'], warea, wnote))


def show (pline, mode='full', showDate=True, tnum=0, mask=[], tleft=0, report=False):
    """ General purpose regiter-line display
    
    Display regiter lines as colour formatter entries with additional data
    such as maximum number of product uses, min/max quantities per ha and more.
    
    Takes a dictionary with this structure:
        date: datetime.datetime.date
        name: string
        qty: float
        unit: string
        *pos: list
        *notes: string
    """
    if mode in 'reg' and 'pos' in list(pline):
        del pline['pos']
    elif mode in 'use':
        if 'pos' not in list(pline):
            return
    if showDate:
        print("")
    pdate = "%s" % pline['date'].strftime("%d/%m/%Y")
    if datetime.datetime.today() < pline['date']:
        pdate = "%s%s%s" % (color.GREEN, pdate, color.END)
    if not showDate:
        pdate = "          "
    pname = "%s%s%s" % (
        color.CYAN, pline['name'].upper().rjust(25), color.END)
    if 'pos' in list(pline):
        productData = products.getData()[pline['name']]
        counter = 1
        for area in pline['pos']:
            if len(mask) > 0 and area not in mask:
                continue
            # quantity per /ha computation
            if counter == len(pline['pos']) and counter > 1:
                pqty = -pline['qty'] - pqty
                pdate = "          "
            else:
                pqty = (-pline['qty'] / \
                        sum([products.areas[x] for x in pline['pos']])) * \
                        products.areas[area]
            sqty = ""
            # Max number of product usage per season
            pnum = getNum(pline['name'].lower(), area, pline['date'], tnum)
            if pnum > productData['num'] and productData['num'] > 0:
                pnumColor = color.RED
            elif pnum == productData['num']:
                pnumColor = color.YELLOW
            else:
                pnumColor = ""
            if productData['num'] == 0:
                pnmax = "-"
            else:
                pnmax = productData['num']
            # Minimum/maximum usage per /ha
            pqmax = pqty/products.areas[area]
            minmax = productData['minmax']
            if pqmax > minmax[1]*1.05:
                pqmaxColor = color.RED
            elif (pqmax > minmax[1] or pqmax < minmax[0]):
                pqmaxColor = color.YELLOW
            else:
                pqmaxColor = ''
            if minmax[0] == minmax[1]:
                ref = " (%.2f %s/ha)" % (minmax[0], pline['unit'])
            else:
                ref = " (%.2f-%.2f %s/ha)" % (
                    minmax[0], minmax[1], pline['unit'])
            pqmax = "%s%.2f%s %s/ha%s" % (
                pqmaxColor, pqmax, color.END, pline['unit'], ref)
            # auto-computation
            if pline['qty'] == 0 or pline['qty'] == -0:
                sqty = '-'.join(["%.2f" % (x*products.areas[area]) for x in productData['minmax']]).rjust(11)
                pqty = 0
                pqmax = ""
            else:
                sqty = "%6.2f" % pqty
            if report:
                if 'notes' in list(pline):
                    pnotes = pline['notes']
                else:
                    pnotes = ""
                if trattamento[area][-1]['date'] != pline['date']:
                    trattamento[area] = buildTrattamento(trattamento[area])
                trattamento[area][-1]['date'] = pline['date']
                trattamento[area][-1]['names'].append(pline['name'].upper())
                trattamento[area][-1]['qtys'].append(pqty)
                trattamento[area][-1]['unit'].append(pline['unit'])
                trattamento[area][-1]['area'] = products.areas[area]
                for entry in productData['obiettivo']:
                    trattamento[area][-1]['target'].append(entry)
                trattamento[area][-1]['titolare'] = "Damiano Barbon"
                if 'notes' in list(pline):
                    trattamento[area][-1]['notes'].append(pline['notes'])
            else:
                # Print to screen usage form
                print("%s %s %s %s | %s%d%s/%s %s <- %s" % (
                    pdate, pname, sqty, pline['unit'].ljust(2),
                    pnumColor, pnum, color.END, pnmax, pqmax, area))
            counter += 1
    else:
        pleft = getRemaining(pline['name'].lower(), pline['date'], tleft)[0]
        if pline['qty'] < 0:
            pqtyColor = color.RED
        else:
            pqtyColor = ""
        if 'notes' in list(pline):
            pnotes = "  %s# %s%s" % (color.GRAY, pline['notes'], color.END)
        else:
            pnotes = ""
        # Print to screen register form
        print("%s %s %s%6.2f%s %s | %6.2f %s %s" % (
            pdate, pname, pqtyColor, pline['qty'], color.END,
            pline['unit'].ljust(2), pleft, pline['unit'], pnotes))
    if pline['qty'] == 0 or pline['qty'] == -0:
        quit(0)


def buildTrattamenti ():
    trattamento = {}
    for area in products.areas:
        trattamento[area] = []
        trattamento[area] = buildTrattamento(trattamento[area])
    return trattamento

def buildTrattamento (item):
    item.append({
        'date': datetime.datetime.today(),
        'names': [],
        'qtys': [],
        'unit': [],
        'area':  0,
        'target': [],
        'titolare': "",
        'notes': []})
    return item

def readSource (file='registro.txt'):
    """ Populate regiter.data
    
    Reads the register line by line and compiles the register.data with
    productLine dictionaries.
    """
    counter = 0
    with open(file, encoding='utf-8') as fp:
        raw = fp.read().splitlines()
    for line in raw:
        data[counter] = {}
        prog = lineaRegistro
        result = prog.match(line)
        data[counter]['date'] = readDate(result.group(1))
        data[counter]['name'] = result.group(2).lower()
        unit, qty = unitConversion(result.group(4).lower(), result.group(3))
        data[counter]['qty'] = qty
        data[counter]['unit'] = unit
        if qty < 0:
            data[counter]['pos'] = products.validate.pos(result.group(5))
        if result.group(6):
            data[counter]['notes'] = result.group(6)
        counter += 1
    

def getNum (product, area, date, offset=0):
    if len(list(data)) == 0:
        readSource()
    counter = offset
    for item in data:
        if (data[item]['name'] == product.lower() and data[item]['qty'] < 0 and
            area.lower() in data[item]['pos'] and date >= data[item]['date']):
            counter += 1
    return counter


def getRemaining (product, date=datetime.datetime.today(), offset=0):
    unit = None
    if len(list(data)) == 0:
        readSource()
    counter = offset
    for item in data:
        if (data[item]['name'] == product.lower() and 
            date >= data[item]['date']):
            counter += data[item]['qty']
            unit = data[item]['unit']
    if not unit:
        unit = 'A'  # this doesn't actually matter since it means the product was never bought before
    return (counter, unit)


def read (mode='reg', search="", file='registro.txt', report=False):
    readSource(file)
    awfulList = [[x, data[x]['date']] for x in list(data)]
    #TODO Add reverse sorting
    awfulList.sort(key=getKey)
    tmpDate = ""
    if report:
        global trattamento
        trattamento = buildTrattamenti()
    for index in [x[0] for x in awfulList]:
        # rimuovi erbicidi per il report
        if report and 'Erbicida' in products.getData()[data[index]['name']]['obiettivo']:
            continue
        if len(search) > 0:
            counter = 0
            mask = []
            for item in search.split(' '):
                if item.lower() in products.areas:
                    mask.append(item.lower())
            for item in list(data[index]):
                for entry in search.split(' '):
                    if str(data[index][item]).count(entry):
                        counter += 1
            if counter == 0:
                continue
        if mode == 'reg':
            if tmpDate != data[index]['date']:
                showDate = True
                tmpDate = data[index]['date']
            else:
                showDate = False
            show(data[index], mode='reg', showDate=showDate)
        else:
            if data[index]['qty'] < 0:
                if tmpDate != data[index]['date']:
                    showDate = True
                    tmpDate = data[index]['date']
                else:
                    showDate = False
                show(data[index], mode='use', showDate=showDate, mask=mask, report=report)
    if len(search) == 0:
        print("\n%s" % ('-'*10))
        for product in list(products.getData()):
            pleft = getRemaining(product)
            if pleft[0] > 0.001 or pleft[0] < -0.001:
                print("%s%s%s %5.2f %s" % (
                    color.CYAN, product.upper(), color.END, pleft[0], pleft[1]))
    elif not report:
        print('-'*10)
        pdata = products.getData()
        carenze = {}
        for item in search.split(' '):
            if item.lower() in products.areas:
                carenze[item.lower()] = 0
        for index in [x[0] for x in awfulList]:
                if 'pos' in list(data[index]):
                    for pos in data[index]['pos']:
                        if pos in list(carenze):
                            offset = (datetime.datetime.today() - data[index]['date']).days
                            if pdata[data[index]['name']]['carenza'] - offset > carenze[pos]:
                                carenze[pos] = pdata[data[index]['name']]['carenza'] - offset
        for area in list(carenze):
            print("Carenza corrente (%s): %d" % (area, carenze[area]))
    if report:
        counter = 1
        for area in products.areas:
            printReport(trattamento[area], offset=counter, area=area)
            counter += 1
            print("\n\n\n\n\n")
        


def printReport (tList, ty=360, offset=1, area=""):
    with open('svg_template.svg', encoding='utf-8') as fp:
        intro = fp.read().splitlines()
    pageCount = 1
    currentDocument = []
    isLastOne = False
    for lineDict in tList[1:]:
        # calcola altezze prima di stampare (margine basso pagina)
        if ty + 18 * len(lineDict['names']) + 12 > 700:
            with open('scheda_B(%d).svg' % (pageCount + offset*10), 'w', encoding='utf-8') as fp:
                for line in intro:
                    fp.write("%s\n" % line)
                traduzione = {
                    'pinot': 'Pinot Grigio',
                    'prosecco': 'Glera',}
                fp.write("<text x=\"274\" y=\"233\" class=\"scheda\" text-anchor=\"end\">%s</text>\n" % ("%.4f" % products.areas[area]).replace('.', ','))
                fp.write("<text x=\"736\" y=\"213.5\" class=\"titoli\" text-anchor=\"end\">%s</text>\n" % traduzione[area])
                fp.write("<text x=\"736\" y=\"233\" class=\"scheda\" text-anchor=\"end\">%s</text>\n" % "N/D")
                for line in currentDocument:
                    fp.write("%s\n" % line)
                fp.write("</svg>")
            ty = 360
            pageCount += 1
            currentDocument = []
        elif lineDict == tList[-1]:
            isLastOne = True
        tx = [114, 350, 393, 470, 591, 762, 857]  # text alignment 'x' values
        lx = [71, 157, 356, 429, 510, 671, 851, 1011]
        ry = 18  # text lines spacing
        oy = 12  # row offset
        tdef = "class=\"scheda\" text-anchor=\"middle\""
        counter = 1
        maxCounter = 2
        currentDocument.append("<text x=\"%d\" y=\"%d\" %s>%s</text>" % (
            tx[0], ty + 18 * counter, tdef, lineDict['date'].strftime("%d/%m/%Y")))
        for product in lineDict['names']:
            currentDocument.append("<text x=\"%d\" y=\"%d\" class=\"scheda\" text-anchor=\"end\">%s</text>" % (
            tx[1], ty + 18 * counter, product.upper()))
            counter += 1
        if counter - 1 > maxCounter:
            maxCounter = counter - 1
        counter = 1
        for index in range(len(lineDict['qtys'])):
            qty = lineDict['qtys'][index]
            currentDocument.append("<text x=\"%d\" y=\"%d\" %s>%s %s</text>" % (
            tx[2], ty + 18 * counter, tdef, ("%.2f" % qty).replace('.', ','), lineDict['unit'][index]))
            counter += 1
        if counter - 1 > maxCounter:
            maxCounter = counter - 1
        counter = 1
        currentDocument.append("<text x=\"%d\" y=\"%d\" %s>%s</text>" % (
            tx[3], ty + 18 * counter, tdef, ("%.4f" % lineDict['area']).replace('.', ',')))
        targets = groupStrings(lineDict['target'])
        for target in targets:
            currentDocument.append("<text x=\"%d\" y=\"%d\" %s>%s</text>" % (
                tx[4], ty + 18 * counter, tdef, target))
            counter += 1
        if counter - 1 > maxCounter:
            maxCounter = counter - 1
        counter = 1
        currentDocument.append("<text x=\"%d\" y=\"%d\" %s>%s</text>" % (
            tx[5], ty + 18 * counter, tdef, lineDict['titolare']))
        currentDocument.append("<text x=\"%d\" y=\"%d\" %s>%s</text>" % (
            tx[5], ty + 18 * (counter + 1), tdef, "Arcade 13/06/1960"))
        #TODO: Note
        counter = 1
        allnotes = groupStrings(lineDict['notes'])
        for allnote in allnotes:
            wordcount = 0
            wordidxbase = 0
            for wordidx in range(len(allnote.split())):
                wordcount += len(allnote.split()[wordidx]) + 1
                if wordcount > 25:
                    print(allnote.split()[wordidx])
                    currentDocument.append("<text x=\"%d\" y=\"%d\" class=\"scheda\" text-anchor=\"start\">%s</text>" % (
                        tx[6], ty + 18 * counter, ' '.join(allnote.split()[wordidxbase:wordidx])))
                    counter += 1
                    wordcount = len(allnote.split()[wordidx]) + 1
                    wordidxbase = wordidx
            currentDocument.append("<text x=\"%d\" y=\"%d\" class=\"scheda\" text-anchor=\"start\">%s</text>" % (
                tx[6], ty + 18 * counter, ' '.join(allnote.split()[wordidxbase:])))
            counter += 1
        if counter - 1 > maxCounter:
            maxCounter = counter - 1
        # > line end <
        tm = ty + maxCounter * 18 + 12
        for value in lx:
            currentDocument.append("<line x1=\"%d\" y1=\"%d\" x2=\"%d\" y2=\"%d\" stroke=\"black\" stroke-width=\"0.70\" />" % (value, ty, value, tm))
        ty = tm
        currentDocument.append("<line x1=\"71\" y1=\"%d\" x2=\"1011\" y2=\"%d\" stroke=\"black\" stroke-width=\"0.70\" />" % (ty, ty))
        if isLastOne:
            with open('scheda_B(%d).svg' % (pageCount + offset*10), 'w', encoding='utf-8') as fp:
                for line in intro:
                    fp.write("%s\n" % line)
                traduzione = {
                    'pinot': 'Pinot Grigio',
                    'prosecco': 'Glera',}
                fp.write("<text x=\"274\" y=\"233\" class=\"scheda\" text-anchor=\"end\">%s</text>\n" % ("%.4f" % products.areas[area]).replace('.', ','))
                fp.write("<text x=\"736\" y=\"213.5\" class=\"titoli\" text-anchor=\"end\">%s</text>\n" % traduzione[area])
                fp.write("<text x=\"736\" y=\"233\" class=\"scheda\" text-anchor=\"end\">%s</text>\n" % "N/D")
                for line in currentDocument:
                    fp.write("%s\n" % line)
                fp.write("</svg>")
            ty = 360
            pageCount += 1
            currentDocument = []
            isLastOne = False


def groupStrings (lala):
    groups = []
    seen = set()
    result = []
    for item in lala:
        if item not in seen:
            seen.add(item)
            result.append(item)
    lala = result
    while len(lala) > 0:
        test = lala[0]
        line = [lala[0]]
        for item in lala[1:]:
            test = test + ", " + item
            if len(test) <= 24: # 22 caratteri è arbitrario
                line.append(item)
            else:
                test = ', '.join(line)
        groups.append(', '.join(line))
        ref = len(lala)
        for index in range(ref):
            if lala[ref-1-index] in line:
                del lala[ref-1-index]
    return groups
