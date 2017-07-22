#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys

import products
import register


def cliHandler (args):
    helpArguments = ['help', 'aiuto']
    if len(args) <= 1:
        print("HELP")
    elif len(args) > 1:
        # parse --quiet option
        for index in list(range(len(args[2:]))):
            if args[index] == '--quiet':
                del args[index]
                pquiet = True
            else:
                pquiet = False
        # parte 'add' meta-command
        if args[1].lower() in ['add', 'agg']:
            if len(args) == 2 or args[2].lower() in helpArguments:
                print("add HELP")
                quit(0)
            else:
                register.add(' '.join(args[2:]), 'add', quiet=pquiet)
        # parse 'use' meta-command
        elif args[1].lower() in ['use', 'uso']:
            if len(args) == 2 or args[2].lower() in helpArguments:
                print("use HELP")
                quit(0)
            else:
                register.add(' '.join(args[2:]), 'use', quiet=pquiet)
        elif args[1].lower() in ['reg']:
            if len(args) == 3 and args[2].lower() in helpArguments:
                print("reg HELP")
                quit(0)
            rmode = 'reg'
            for index in list(range(len(args[2:]))):
                if args[index+2] in products.areas:
                    rmode = 'use'
                    break
            register.read(rmode, ' '.join(args[2:]))
        #TODO: vvv -NOT DONE YET- vvv
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
                

products.read()
cliHandler(sys.argv)
#TODO bal and reg
