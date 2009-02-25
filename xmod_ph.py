#!/usr/local/bin/python
# -*- python -*-
## $Id: xmod_ph.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

import asyncore
import asynchat
import socket
import re

from xmsg import Msg
from xtools import print_traceback

class Client(asynchat.async_chat):
    def __init__(self, config, user, name, command):
        asynchat.async_chat.__init__(self)
        self.user = user
	self.name = name
        if self.name == 'ph':
	    self.name = 'Ph'

        self.phserver = 'ns.uiuc.edu'
        for opt, val in config.iteritems():
            if opt in ('phserver',):
                setattr(self, opt, val)

        self.command('ph', '', command)

    def command(self, tag, dst, txt):
        tag = tag.upper()
        if tag == 'CLEAR':
            self.shutdown()
        elif tag == 'PH':
            self.target = txt
            user_host = txt.split('@', 1)
            if len(user_host) == 1:
                self.ph_user = user_host[0]
                host = self.phserver
            else:
                self.ph_user, host = user_host
            self.buffer = ''
            self.terminator = '\n'
	    try:
		self.close()
  	    except:
		pass
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect((host, 105))

    def window_callback(self,name,win):
        win.maxdepth = 100

    def handle_connect(self):
        self.result_index = 1
        self.push('ph %s\r\n' % self.ph_user)

    def handle_close(self):
        asynchat.async_chat.handle_close(self)
        self.found_terminator()

    def handle_error(self):
        print_traceback()
        #self.user.queue(Msg(self.name, 'fail', '', self.target, asyncore.compact_traceback()))
        self.user.queue(Msg(self.name, 'fail', '', self.target, 'connection failed'))

    def collect_incoming_data(self, data):
        self.buffer = self.buffer + data

    def found_terminator(self):
        line = self.buffer
        tag = 'fmsg'
        try:
            if line[0] == '-': # multiline response
                line = line[1:]
            if line[3] == ':': # OK, see RFC 2378 for codes
                codestart = line[0]
                if codestart in ('13'): tag = 'info'
                elif codestart in ('45'): tag = 'fail'
                line = line[4:]
                dmatch = re.match('(\d+):', line)
                if dmatch:
                    result_index = int(dmatch.group(1))
                    if result_index != self.result_index: # output separator
                        self.result_index = result_index
                        self.user.queue(Msg(self.name, 'fmsg', '', self.target, ' '))
                    line = line[dmatch.end():]
                else:
                    self.result_index = 1
                line = line.strip()
                if line[0] == ':': # continued field
                    line = '         %s' % line[1:]
        except: # invalid format
            print 'Ph response invalid:', self.buffer
            pass
        self.user.queue(Msg(self.name, tag, '', self.target, line))
        self.buffer = ''

    def shutdown(self):
        try:
            self.close()
        except:
            pass
