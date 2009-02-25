#!/usr/local/bin/python
# -*- python -*-
## $Id: thisusedtobe_xmod_send.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms


from xtools import print_traceback;

class Client:
    def __init__(self, config, user, command):
        self.user = user;
        self.command('send','%server',command)

    def command(self, tag, dst, txt):
        try:    
            out = eval(txt);
        except:
            self.user.session.ERROR('Evaluation exception: '+txt)
            return

        self.user.session.INFO(txt+'='+str(out));


    def shutdown(self):
        return
