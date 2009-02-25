#!/usr/local/bin/python
# -*- python -*-
## $Id: xmod_turn.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

import os

class Client:
    def __init__(self, config, user, name, command):
        self.user = user
        self.turncmd = 'br'
        for opt, val in config.iteritems():
            if opt in ('turncmd',):
                setattr(self, opt, val)
        self.command('send','%server', command)

    def command(self, tag, dst, txt):

        # purify command

        txt = txt.lower()
        purecmd = ''
        for i in range(len(txt)) :
            if txt[i] in "abcdefghijklmnopqrstuvwxyz 0123456789" :
                purecmd=purecmd+txt[i]

        cmd = '%s %s' % (self.turncmd, purecmd)

        args = cmd.split(' ')
        os.spawnvp(os.P_NOWAIT, args[0], args)

    def shutdown(self):
        pass

    def window_callback(self, name, win):
        pass
