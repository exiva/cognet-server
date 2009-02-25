#!/usr/local/bin/python
# -*- python -*-
## $Id: xmod_timestamp.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

import xmsg
import time
import os

from xtools import boolean_from_input

OPTIONS = ('timestamp', 'timeformat', 'timezone')

# timezone support may or may not work on python versions before 2.3,
# depending on your system libraries.

# also, timezone stuff is not thread-safe.

class Client:
    def __init__(self, config, user, name, command):
        self.user = user
        self.timestamp = 1
        self.timeformat = '%H:%M.%S'
	self.timezone = ''

        for opt, val in config.iteritems():
            if opt in OPTIONS:
                setattr(self, opt, val)

        self.command('send', '%server', command)

    def command(self, tag, dst, txt):
        if '%' in txt:
            self.timestamp = 1
            self.timeformat = txt
            self.user.session.INFO(">> set timestamp format to '%s'" % txt)
        else:
            if not hasattr(self, 'inited') and txt == '':
                pass
            else:
                self.timestamp = boolean_from_input(self.timestamp, txt)
                self.user.session.INFO('>> timestamp display %s' %
                ("disabled","enabled with format '%s'" % self.timeformat)[self.timestamp])
        self.inited = 1

    def shutdown(self):
        return

    def window_callback(self, name, win):
        return

    def input_hook(self, serial, tag, app, name, txt):
        return ( serial, tag, app, name, txt )

    def output_hook(self, msg):
        if self.timestamp:

	    # save system timezone
	    old_timezone = os.environ.get('TZ') 

	    # set user timezone
	    if self.timezone:
	        os.environ['TZ'] = self.timezone

	    if hasattr(time, 'tzset'):
	    	time.tzset()

            ts = time.strftime(self.timeformat)
            tag = msg.tag
            if tag == 'dmsg':
                msg.tag = 'fmsg'
                msg.txt = '%s %s> %s ' % (ts, msg.src, msg.txt)
            elif tag == 'dmsg/act':
                msg.tag = 'fmsg'
                msg.txt = '%s %s %s ' % (ts, msg.src, msg.txt)
            elif tag == 'smsg':
                msg.tag = 'fmsg'
                msg.dst, msg.src = msg.src, msg.dst
                msg.txt = '%s %s> %s ' % (ts, msg.dst, msg.txt)
            elif tag == 'smsg/act':
                msg.tag = 'fmsg'
                msg.dst, msg.src = msg.src, msg.dst
                msg.txt = '%s %s %s ' % (ts, msg.src, msg.txt)
            elif tag == 'info':
                msg.txt = '%s %s' % (ts, msg.txt)

	    # restore timezone
            if os.environ.has_key('TZ'):
	        del os.environ['TZ']

	    if old_timezone:
		os.environ['TZ'] = old_timezone

	    if hasattr(time, 'tzset'):
	    	time.tzset()

        return msg
