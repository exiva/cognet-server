#!/usr/local/bin/python
# -*- python -*-
## $Id: xmod_skel.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms


import xmsg

class Client:
    def __init__(self, config, user, name, command):
        self.user = user;
	self.name = name;
        self.command('send','%server', command)

    def command(self, tag, dst, txt):
        return

    def shutdown(self):
        return

    def window_callback(self, name, win):
        return

    def input_hook(self, serial, tag, app, name, txt):
        return ( serial, tag, app, name, txt )

    def output_hook(self, msg):
        return msg
