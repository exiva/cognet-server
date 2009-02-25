#!/usr/local/bin/python
# -*- python -*-
## $Id: xmain.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

import asyncore
import xserver
import xuser

from xtools import print_traceback

# Server portnumber
#
PORT = 4000

# If savestate is nonzero, the server will attempt
# to save user session state on shutdown. experimental.
#
SAVESTATE = 0

# IP address that clients may connect from
# (you should probably adjust this to your needs)
#
ALLOWED_ADDRS = [
    '127.0.0.1', # localhost
    '199.106.69.146', # danger trial nat
    '63.203.215.64',  # danger firewall
    '64.168.138.218', # mountainview.frotz.net
    ]

if __name__ == '__main__':

    print "<< server start >>"

    # Add as many users as you need
    # (use the mkpasswd.py tool to generate the password hashes)
    #
    # You should probably add users to config.py, to prevent
    # cvs merge problems.  Read config.py.dist.
    #
    #xuser.User({
    #   "ircserver" : "irc.catch22.org",
    #   "ircport" : 6667,
    #   "ircuser" : "guest",
    #   "ircname" : "Guest User",
    #   "ircnick" : "testuser",
    #   "name" : "guest",
    #   "passwd" : "570a90bfbf8c7eab5dc5d4e26832d5b1" # fred
    #   })
    #
    try:
        import config
        for setting in ('PORT','SAVESTATE','ALLOWED_ADDRS'):
            if hasattr(config,setting):
                locals()[setting]=getattr(config,setting)
    except ImportError:
        pass



    print "<< %d user records >>" % len(xuser.USERS)
    
    xserver.Server('', PORT, ALLOWED_ADDRS)
    
    try:
        xserver.loop()
    except:
        print "<< error >>"
        print_traceback()
        if SAVESTATE:
            print "<< saving user state >>"
            for name in xuser.USERS:
                user = xuser.USERS[name]
                user.savestate()
        print "<< server exiting >>"
