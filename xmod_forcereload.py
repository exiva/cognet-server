#!/usr/local/bin/python
# -*- python -*-
## $Id: xmod_forcereload.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

from xtools import print_traceback

class Client:
    def __init__(self, config, user, command):
        self.user = user
	self.command('reload','%server',command)

    def command(self, tag, dst, command):
        module = 'xmod_'+command
        try:    
            print '<< reloading', module+',',
            exec "import %s" % module
            exec "reload(%s)" % module  
            self.user.session.INFO(">> Module '%s' reloaded." % command)
            print "success >>"
        except:
            print "failed >>"
            print_traceback();
            self.user.session.ERROR("Module '%s' failed to reload." % command)

        return

    def shutdown(self):
        return
