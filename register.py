#!/usr/bin/env python
# prodotti.py


import re
import datetime
import products
from tools import readDate, unitConversion, ProductException, color, query_yes_no, getKey


data = {}
lineaRegistro = re.compile('([0-9/]*) (.*) (-*[.0-9]+)[ ]*([mMkK]*[lLgG])[ ]*[-<]*([^# ]*)[ ]*[#]*[ ]*(.*)')

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
    unit, qty = unitConversion(result.group(4).lower(), result.group(3))
    if metodo == 'use' and qty > 0:
        qty = qty * (-1)
    productLine['qty'] = qty
    if qty < 0:
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
            warea = " <- %s" % ','.join(productLine['pos'])
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


def show (pline, mode='full', showDate=True, tnum=0, mask=[], tleft=0):
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
        color.CYAN, pline['name'].upper().rjust(18), color.END)
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
            if (pqmax > minmax[1]*1.05 or pqmax < minmax[0]*0.95):
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
            # Print to screen usage form
            print("%s %s %6.2f %s | %s%d%s/%s %s <- %s" % (
                pdate, pname, pqty, pline['unit'].ljust(2),
                pnumColor, pnum, color.END, pnmax, pqmax, area))
            counter += 1
    else:
        pleft = getRemaining(pline['name'].lower(), pline['date'], tleft)
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
    if len(list(data)) == 0:
        readSource()
    counter = offset
    for item in data:
        if (data[item]['name'] == product.lower() and 
            date >= data[item]['date']):
            counter += data[item]['qty']
    return counter


def read (mode='reg', search="", file='registro.txt'):
    readSource(file)
    awfulList = [[x, data[x]['date']] for x in list(data)]
    #TODO Add reverse sorting
    awfulList.sort(key=getKey)
    tmpDate = ""
    for index in [x[0] for x in awfulList]:
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
                show(data[index], mode='use', showDate=showDate, mask=mask)
    #TODO: vvvvv -From this line onward- vvvvv
    quit(0)
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
