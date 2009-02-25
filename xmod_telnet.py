#!/usr/local/bin/python
# -*- python -*-
## $Id: xmod_telnet.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

import asyncore
import asynchat
import socket
import string

from xmsg import Msg
from xtools import print_traceback
from string import lower

class Client:
    def __init__(self, config, user, name, command):
        self.channel = None
        self.user = user
	self.name = name;
	if( name == 'telnet' ) :
	    name = 'TELNET'

        self.lastctxt = ""
        for name in config:
            if name.startswith("telnet"):
                self.__dict__[name] = config[name]
        self.cmd_CONNECT('','',command);

    def shutdown(self):
        try :
            self.channel.close();
        except:
            pass ;

        print "<< TELNET window cleared disconnect >>"
        self.channel.handler = None
        self.channel = None
    
    def window_callback(self,name,win):
        print 'telnet window callback',name,win
        win.maxdepth = 100;
        return

    def __getitem__(self, item):
        return self.__dict__.get(item)
        
    def connect(self,host,port):
        if self.channel:
            self.ERROR("<< already online >>")
        else:
            self.lastctxt = ""
            self.INFO("<< connecting to '%s:%d' >>" % (host,port))
            self.channel = Channel(
                self,host,port,'\r\n')
    
    def push(self, line):
        self.channel.push(line + '\r\n')

    def REPLY(self, ctxt, text):
        self.user.queue(Msg(self.name,"repl","",ctxt,text))
        
    def ERROR(self, ctxt, text):
        self.user.queue(Msg(self.name,"fail","",ctxt,text))

    def INFO(self, text):
        self.user.queue(Msg(self.name,"info","","",text))

    def DISP(self, ctxt, text):
        self.user.queue(Msg(self.name,"info","",ctxt,text))

    def SEND(self, tag, ctxt="", text=""):
        self.user.queue(Msg(self.name, tag, "",ctxt, text))
    
        
    def handle_close(self):
        print "<< disconnect >>"
        self.channel.handler = None
        self.channel = None
        self.INFO("<< disconnected >>")

    def handle_connect(self):
        print "<< connect >>"
        self.INFO("<< connected >>")        
        
    def handle_line(self, data):
        self.INFO(data);

    def badcommand(self, tag, ctxt, args):
        self.ERROR(ctxt, "unknown command '%s'" % tag)
        
    def command(self, tag, dst, txt):
        if not tag: return
        
        # make sure we're all upper case so lookups work
        #
        tag = tag.upper()

        # Keep track of the last context we issued a command from 
        #
        if len(dst) > 0:
            self.lastctxt = dst
        
        # pass raw commands directly to the server
        #
        if tag[0] == '/':
            self.push(tag[1:] + ' ' + txt + '\n')
            return
        
        try:
            getattr(self, 'cmd_'+tag,self.badcommand)(tag, dst, txt)
        except:
            print "<< command() failure >>"
            print_traceback()

    def cmd_TEL(self, tag, ctxt, args):
        cmd_CONNECT(self, tag, ctxt, args);

    def cmd_CONNECT(self, tag, ctxt, args):
        ( host , port ) = args.split(' ');
        port = int(port);
        self.connect(host,port);

    def cmd_SEND(self, tag, ctxt, args ) :
        self.push(args);

    def unpack2(self, args):
        n = args.find(' ')
        if n == -1:
            return args, ''
        else:
            return args[:n], args[n+1:] 

class Channel (asynchat.async_chat):
    def __init__(self, handler, host, port, terminator):
        asynchat.async_chat.__init__(self)
        self.set_terminator(terminator)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.handler = handler
        self.buffer = ''
        handler.channel = self
        self.connect((host,port))

    def handle_connect(self):
        self.handler.handle_connect()
            
    def handle_close(self):
        if self.handler:
            self.handler.handle_close()
            self.producer_fifo.push(None)
        #else:
        #   print "<< huh? already closed. >>"
            
    def handle_expt(self):
	pass

    def handle_error(self):
	pass
        
    def found_terminator(self):
        try:
            self.handler.handle_line(self.buffer)
        except:
            print_traceback()
        self.buffer = ''

    def collect_incoming_data(self, data):
        self.buffer = self.buffer + data
