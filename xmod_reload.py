#!/usr/local/bin/python
# -*- python -*-
## $Id: xmod_reload.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

import sys
from xtools import print_traceback

class Client:
    def __init__(self, config, user, name, command):
        self.user = user
	self.command('reload', '%server', command)

    def command(self, tag, dst, command):
        try:
            print '<< reloading', command,
            modname = 'xmod_%s' % command
            modules = self.user.modules
            for as in modules.keys():
                if modules[as].__class__.__module__ == modname:
                    self.user.stop_module(as)
            if sys.modules.has_key(modname):
                del sys.modules[modname]
            module = __import__(modname, globals(), locals())
            self.user.session.INFO(">> Module '%s' reloaded" % command)
            print "succeeded >>"
        except:
            print "failed >>"
            print_traceback()
            self.user.session.ERROR("Module '%s' failed to reload" % command)

        return

    def shutdown(self):
        return
