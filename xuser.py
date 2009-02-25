#!/usr/local/bin/python
# -*- python -*-
## $Id: xuser.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

import md5
import xmsg
import time

from xtools import print_traceback
from string import find

import pickle

def hex_digest(s):
    return md5.new(s).hexdigest()

USERS = {}

def locate(session, name, passwd):
    user = USERS.get(name)
    
    if not user:
        return None

    if user.passwd != hex_digest(passwd):
        return None

    user.attach(session)
    return user


class Window:
    def __init__(self, app, name, devicename, queuelen):
        self.devicename = devicename
        self.name = name
        self.app = app
        self.queue = []
        self.maxdepth = queuelen

class User:
    def __init__(self, config=None, **kw):
        if not config:
            config = kw
        self.name = config["name"]
        self.passwd = config["passwd"]

        del config["passwd"]

        self.queuelen = config["def_queuelen"]
        self.startup_cmds = config.get('startup_cmds', ())
        
        self.session = None
        self.config = config
        self.client_settings = {}
        self.modules = {}
        self.outbound = []
        self.windows = {}
        self.serial = 1

        self.loadstate()
        self.token = None
        USERS[self.name] = self

    def savestate(self):
        if self.outbound:
            fp = open("user.%s.dat" % self.name,"w")
            p = pickle.Pickler(fp)
            p.dump(self.outbound)
            fp.flush()
            fp.close()

    def loadstate(self):
        try:
            fp = open("user.%s.dat" % self.name,"r")
            try:
                p = pickle.Unpickler(fp)
                msgs = p.load()
                fp.close()
                for m in msgs:
                    self.queue(m)
            finally:
                fp.close()
        except:
            print_traceback()
            print "<< cannot load state for '%s' >>" % self.name

    def attach(self, session):

        # create a token to uniquely identify this user
        # across the lifetime of the server
        #
        if not self.token:
            self.token = hex_digest(time.time().__str__() + repr(session.addr))
            print "<< %s >>" % self.token

        # detach any existing sessions
        #
        if self.session:
            self.session.disconnect()
            
        self.session = session

        if self.token == session.token:
            lastseen = session.serial
        else:
            lastseen = -1
        session.status("sync",self.token,"")
    
        for item in self.client_settings:
            session.status("set",item,self.client_settings[item])

        for msg in self.outbound:
            if msg.serial > lastseen:
                msg.send(session)

        if not hasattr(self, 'was_attached'):
            for cmd in self.startup_cmds:
                tagtxt = cmd.split(' ', 1)
                if len(tagtxt) > 1:
                    tag, txt = tagtxt
                else:
                    tag = tagtxt[0]
                    txt = ''
                self.command(None, tag, '%server', txt)
            self.was_attached = 1
            
    def detach(self, session):
        if self.session == session:
            self.session = None

    def getwindow(self, app, name):
        if not name: name = ""
        if not app: app = ""

        devicename = app+' '+name
    
        app = app.lower()

        win = self.windows.get(app+' '+name)
        if not win:
            # create window
            win = Window(name,app,devicename,self.queuelen)
            self.windows[app+' '+name] = win
        
            # window creation callback into application
            svr = self.modules.get(app.lower())

            if svr and hasattr(svr, 'window_callback'):
                try:
                    svr.window_callback(name,win)
                except:
                    print '<< Window callback exception in %s >>' % app
                    print_traceback()
        return win

    def checkwindow(self, app, name):
        if not name: name = ""
        if not app: app = ""

        app = app.lower()
        name = name.lower()

        win = self.windows.get(app+' '+name)
        
        return win

    def deletewindow(self, app, name):  
        winname = '%s %s' % (app.lower(), name.lower())
        self.session.status("kill",self.windows[winname].devicename,"")
        del self.windows[app+' '+name]
        

    def getappname(self, name):
        endname = find(name,' ')
        if endname == -1 :
            return name.lower()
        else:
            return name[:endname].lower()

    def getwinname(self, name):
        endname = find(name,' ')

        if endname == -1 :
            return ''
        else:
            return name[endname+1:]

    def clearappwindows(self, app):
        app = app.lower()

        list = self.windows.keys(); 

        for w in list :
            appname = self.getappname(w) 
            winname = self.getwinname(w)
            win = self.windows.get(w)

            if app.lower() == appname:
                for msg in win.queue:
                    self.outbound.remove(msg)
                    win.queue = []

                self.deletewindow(appname, winname)
        return
            
    def queue(self, msg):
        # let the modules hook the queue

        for m in self.modules:
            module = self.modules[m]
            if hasattr(module, 'output_hook'):
                try:
                    msg = module.output_hook(msg)
                except:
                    print "<< output callback failure >>"
                    print_traceback()

        # did a module eat the message?
        if msg == None: 
            return

        # all messages get a serial number
        #
        msg.serial = self.serial
        self.serial = self.serial + 1

        # Some message types should never be queued.
        #
        if msg.tag == 'show':
            if self.session:
                msg.send(self.session)
            return

        # All other messages get queued in the master queue
        #
        self.outbound.append(msg)

        # smsg style messages are displayed in the source
        # window, not the destination window
        #
        if (msg.tag == 'smsg') or (msg.tag == 'smsg/act'):
            win = self.getwindow(msg.app,msg.src)
        else:
            win = self.getwindow(msg.app,msg.dst)

        # attach the message to the queue of its window
        # enforce the per-window maxdepth of the queue
        #
        win.queue.append(msg)
        if (win.maxdepth > 0) and (len(win.queue) == win.maxdepth):
            old = win.queue.pop(0)
            self.outbound.remove(old)

        # If we're online, send it down
        #
        if self.session:
            msg.send(self.session)

    def stop_module(self, app):
        module = self.modules.get(app.lower())
        if module:
            try: 
                self.modules[app].shutdown()
            except :
                print_traceback() 

            del self.modules[app]

        self.clearappwindows(app)
        
    def command(self, serial, tag, dst, txt):
        #print 'tag: '+tag
        #print 'dst: '+dst
        #print 'txt: '+txt

        app = self.getappname(dst)
        name = self.getwinname(dst)

        # the following server stuff can't be eaten by modules.

        if tag == "clear":
            if name == '':   # Deleting a module window
                self.stop_module(app)
                self.session.INFO(">> Module '%s' killed by clear" % app)

            else:
                win = self.checkwindow(app, name)
                if win:
                    for msg in win.queue:
                        self.outbound.remove(msg)
                    win.queue = []
                    self.deletewindow(app, name)

                module = self.modules.get(app.lower())
                if module :
                    try:
                        self.modules[app].command(tag, name, '')
                    except:
                        print_traceback()

                self.session.status("clear",dst,"")
            return


        if tag == "bye":
            self.session.disconnect()
            return

        if tag == "save":
            self.client_settings[dst] = txt
            return

        if tag == "query":
            if dst == "windows":
                for win in self.windows:
                    win = self.windows[win]
                    self.session.INFO(
                        "window '%s' has %d messages" % (win.name,len(win.queue))
                        )
                return


        # is it aimed at the server?

        if dst == '%server' :
	    as = '';		# don't override module name

            if tag == "stop":
                module = self.modules.get(txt.lower())
                if module:
                    module.shutdown()
                    del self.modules[txt]
                    self.clearappwindows(txt)
                    self.session.INFO(">> Module '%s' stopped" % txt)
                else :
                    self.session.ERROR("Module '%s' not running" % txt)

                return

            if tag == "start":
		nameargs = txt.split(' ',1)
		
		if len(nameargs) > 1:
		    tag, txt = nameargs
		else :
		    tag = txt

                module = self.modules.get(tag.lower())
                if module :
                    self.session.ERROR("Module '%s' is already running" % txt)
                    return

	    if tag == "startas" :
		# parse arguments
	  	nameargs = txt.split(' ', 2)
		if len(nameargs) == 1:
                    self.session.ERROR('Syntax: /startas <name> <module> <args>')
                    return
		elif len(nameargs) == 2:
		    as, tag = nameargs; txt = ''
		else:
		    as, tag, txt = nameargs

		# already running?
		module = self.modules.get(as.lower())
		if module:
		    self.session.ERROR("Module named '%s' already running" % txt)
		    return

            # if we don't recognize it, try to send it to a module.
                
	    if as == '':
		as = tag

            sm = self.modules.get(as.lower())
            if sm:
                try:
                    sm.command(tag,as,txt)
                except:
                    print "<< module '%s' command failed >>" % tag
                    print_traceback()
                    self.session.ERROR("Module '%s' command failed" % tag)
            else:
                print '<< loading module "%s" as "%s":' % (tag, as), 
                try:
                    # This "module" is a Python module, not a Client class
                    module = __import__('xmod_%s' % tag, globals(), locals())
                    if tag != as:
                    	self.session.INFO(">> Module '%s' started as '%s'" % (tag, as) )
		    else :
                    	self.session.INFO(">> Module '%s' started" % tag)

                except:
                    print 'load failed >>'
                    print_traceback()
                    self.session.ERROR("Module '%s' failed to load" % tag)
                    return

                try:
                    self.modules[as.lower()] = module.Client(self.config, self, as, txt)
                except:
                    print 'initialization failed >>'
                    print_traceback()
                    self.session.ERROR("Module '%s' failed to initialize" % tag)
                    return

                print 'load successful >>'

            return
            

        # give modules a chance to filter things aimed at windows other
        # than %server.

        for m in self.modules:
            module = self.modules[m]
            if hasattr(module, 'input_hook'):
                try:
                    serial, tag, app, name, txt = \
                            self.modules[m].input_hook(
                                    serial, tag, app, name, txt )
                except:
                    print '<< input callback failure >>'
                    print_traceback()

        # did a module eat the input?
    
        if tag == None:
            return

        # dispatch the command to a module

        sm = self.modules.get(app.lower())
        if sm:
            try:
                sm.command(tag, name, txt)
            except:
                print "<< module '%s' command failed >>" % app
                print_traceback()
                self.session.ERROR("Module '%s' command failure" % app)
        else:
            self.session.ERROR('Application %s not running' % app)

        return
