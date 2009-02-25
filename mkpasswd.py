#!/usr/local/bin/python
# -*- python -*-
## $Id: mkpasswd.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms





import md5
import sys

def hex_digest(s):
	return md5.new(s).hexdigest()

try:
	print '"%s"' % hex_digest(sys.argv[1])
except:
	print "usage: %s <password>" % sys.argv[0]
