#!/usr/local/bin/python
# -*- python -*-
## $Id: xmod_sr.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

# send user input out to client. for client testing.

class Client:
    def __init__(self, config, user, name, command):
        self.user = user;
        self.command('sr','%server',command)

    def command(self, tag, dst, txt):
        print txt
        self.user.session.push(txt + '\n')

    def shutdown(self):
        return
