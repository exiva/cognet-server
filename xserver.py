#!/usr/local/bin/python
# -*- python -*-
## $Id: xserver.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

import asyncore
import asynchat

import string
import socket
import time
import sys

import xuser

class Session (asynchat.async_chat):
    def __init__(self, server, conn, addr, allowed):
        print "<< session connected %s:%d >>" % addr
        asynchat.async_chat.__init__(self,conn)
        self.server = server
        self.addr = addr
        self.set_terminator('\n')
        self.created = int (time.time())
        self.buffer = ''
        self.user = None
        self.mark = ':'
        self.serial = 0
        self.token = None
    
        if addr[0] in allowed:
            return
        else:
            print "<< rejecting %s:%d >>" % addr
            self.push('*** access denied ***\r\n')
            self.teardown()
        
    def teardown(self):
        if self.user:
            self.user.detach(self)
        self.user = None
        self.server = None
        self.close_when_done()
        
    def disconnect(self):
        print "<< session disconnected %s:%d >>" % self.addr
        self.status("info","%server","You have been disconnected.")
        self.teardown()
        
    def handle_close(self):
        if self.server:
            print "<< session terminated %s:%d >>" % self.addr
            self.teardown()
        #else:
        #   print "<< extra close? >>"
        
    def handle_error(self):
        t, v = sys.exc_info()[:2]
        if t is SystemExit:
            raise t, v
        else:
            asynchat.async_chat.handle_error(self)

    def handle_expt(self):
	pass

    def collect_incoming_data(self, data):
        self.buffer = self.buffer + data

    def handle_timeout(self):
        if self.user:
            self.push(":ping:::\n")
        self.timeout = int(time.time()) + 60 #180

    def found_terminator(self):
        data = self.buffer
        self.buffer = ''

        self.timeout = int(time.time()) + 60 #180

        # following code strips all CRs, working around a client bug
        l = len(data)

        ds = data
        data = ''

        for i in range(l) :
            if not (ds[i] == '\r') :
                data = data + ds[i]

#       print 'Raw: ', ds
        print 'Cooked: ', data

        cmd = {}
        # <serial>:<tag>:<dst>:<txt>
        parts = data.split(self.mark)

        l = len(parts)
        if l < 4:
            return

        if l > 4:
            serial, tag, dst = parts[:3]
            txt = string.join(parts[3:],self.mark)
        else:
            serial, tag, dst, txt = parts

        if self.user:
            self.user.command(serial, tag, dst, txt)
        else:
            if tag == 'serial':
                try:
                    self.serial = int(dst)
                    self.token = txt
                except:
                    pass
                return
            if (tag == "auth") or (tag == "user") or (tag == "test"):
                self.user = xuser.locate(self, dst, txt)
                if self.user:
                    self.INFO("User %s connected at %s" % (self.user.name, time.strftime("%H:%M:%S on %Y.%m.%d")))
                else:
                    self.ERROR("bad user or password")
                    self.close_when_done()
            else:
                self.ERROR("unknown command")
                self.close_when_done()

    def INFO(self, text):
        self.push(string.join(['','info','','%server',text],self.mark) + '\n')

    def ERROR(self, text):
        self.push(string.join(['','fail','','%server',text],self.mark) + '\n')
        
    def status(self, tag, dst='', txt=''):
        self.push(string.join(['',tag,'',dst,txt],self.mark) + '\n')

class Server (asyncore.dispatcher):
    def __init__(self, ip, port, allowed):
        self.ip = ip
        self.port = port
        self.allowed = allowed
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((ip, port))

        self.listen(1024)

        host, port = self.socket.getsockname()

    def writable(self):
        return 0

    def readable(self):
        return self.accepting
    
    def handle_read(self):
        pass

    def handle_connect(self):
        pass

    def handle_accept(self):
        try:
            conn, addr = self.accept()
        except socket.error:
            return
        except TypeError:
            return

        Session(self, conn, addr, self.allowed)

def loop():
    map = asyncore.socket_map
    poll_fun = asyncore.poll

    while map:
        poll_fun(15, map)
        now = int(time.time())
        for conn in map.itervalues():
            when = conn.__dict__.get("timeout",-1)
            if when < 0: continue
            if when < now: 
                try:
                    conn.handle_timeout()
                except:
                    print "timeout exception?"

