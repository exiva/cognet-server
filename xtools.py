#!/usr/local/bin/python
# -*- python -*-
## $Id: xtools.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

import sys
import traceback

def print_traceback():
    try:
        ei = sys.exc_info()
        print "OOPS:",ei[0]
        print "OOPS:",ei[1]
        traceback.print_tb(ei[2])
    finally:
        del ei

def boolean_from_input(prevval, input):
    if len(input) == 0:
        return not prevval
    input = input.lower()
    if input.find('on') != -1 or input.find('yes') != -1:
    	return 1
    return 0
