#!/usr/local/bin/python
# -*- python -*-
## $Id: xmod_finger.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

import asyncore
import asynchat
import socket

from xmsg import Msg
from xtools import print_traceback

class Client(asynchat.async_chat):
    def __init__(self, config, user, name, command):
        asynchat.async_chat.__init__(self)
        self.user = user
	self.name = name
	if( self.name == 'finger' ) :
	    self.name = 'Finger'

        self.command('finger', '', command)

    def command(self, tag, dst, txt):
        tag = tag.upper()
        if tag == 'CLEAR':
            self.shutdown()
        elif tag == 'FINGER':
            self.target = txt
            user_host = txt.split('@', 1)
            if len(user_host) == 1:
                self.finger_user = user_host[0]
                host = '127.0.0.1'
            else:
                self.finger_user, host = user_host
            self.buffer = ''
            self.terminator = '\n'
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect((host, 79))

    def window_callback(self,name,win):
        win.maxdepth = 100

    def handle_connect(self):
        self.push('%s\r\n' % self.finger_user)

    def handle_close(self):
        asynchat.async_chat.handle_close(self)
        self.found_terminator()

    def handle_error(self):
        print_traceback()
        #self.user.queue(Msg(self.name, 'fail', '', self.target, asyncore.compact_traceback()))
	self.user.queue(Msg(self.name,'fail','',self.target,'connection failed'))

    def collect_incoming_data(self, data):
        self.buffer = self.buffer + data

    def found_terminator(self):
        self.user.queue(Msg(self.name, 'fmsg', '', self.target, self.buffer))
        self.buffer = ''

    def shutdown(self):
        try:
            self.close()
        except:
            pass

class DemoUser(object):
    def queue(self, msg):
        print msg

if __name__ == '__main__':
    f = Client(None, DemoUser(), 'njriley@acm.uiuc.edu')
    
    asyncore.loop()
