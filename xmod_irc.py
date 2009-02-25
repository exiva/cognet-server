#!/usr/local/bin/python
# -*- python -*-
## $Id: xmod_irc.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

import asyncore
import asynchat
import socket
import re
import time

CHANNEL_LEADERS = '#&+!' # RFC 2812 section 1.3
ARG_MODES = 'Ivokble'

from xmsg import Msg
from xtools import print_traceback, boolean_from_input

class IrcUser:
    def __init__(self, name, ulist):
        self.name = name.lower()
        self.channels = {}
        self.ulist = ulist
        ulist[name] = self

    def destroy(self):
        #print "destroy(%s)" % self.name
        try:
            del self.ulist[self.name]
        except:
            pass
        self.ulist = None

        for n, c in self.channels.iteritems():
            try:
                del c.users[self.name]
            except:
                print "??? %s not on %s (x)" % (self.name,n)
        self.channels = None

    def rename(self, newname):
        for n, c in self.channels.iteritems():
            try:
                del c.users[self.name]
                c.users[newname] = self
            except:
                print "??? %s not on %s (r)" % (self.name,n)
        try:
            del self.ulist[self.name]
            self.ulist[newname] = self
        except:
            pass
        self.name = newname

class IrcChannel:
    def __init__(self, name, clist):
        self.name = name.lower()
        self.users = {}
        self.modes = {}
        self.clist = clist
        clist[name] = self

    def add(self, user):
        self.users[user.name] = user
        user.channels[self.name] = self

    def destroy(self):
        #print "destroy(%s)" % self.name
        try:
            del self.clist[self.name]
        except:
            pass
        self.clist = None

        for n in self.users:
            try:
                u = self.users[n]
                del u.channels[self.name]
                if not u.channels:
                    u.destroy()
            except:
                pass
        self.users = None

    def key(self):
        return modes.get('k', '')

    def remove(self, user):
        try:
            del user.channels[self.name]
        except:
            print "??? %s not on %s (u)" % (user.name, self.name)
        if not user.channels: user.destroy()
        try:
            del self.users[user.name]
        except:
            print "??? %s not on %s (c)" % (user.name, self.name)

    def modestr(self, mstr):
        if mstr[0] not in '+-':
            print '*** unknown channel mode string', mstr
            return
        mstr = mstr.rstrip()
        arg_start_pos = mstr.find(' ')
        if arg_start_pos == -1:
            mchars = mstr
            margs = ()
        else:
            mchars = mstr[:arg_start_pos]
            margs = mstr[arg_start_pos + 1:].split(' ')
            margs.reverse()
        modes = self.modes
        for c in mchars:
            if c == '-':
                neg = 1
            elif c == '+':
                neg = 0
            elif c in ARG_MODES:
                if c in 'kl': # +l <limit>, -l, +k <key>, -k *
                    if neg:
                        del modes[c]
                        if c == 'k': margs.pop()
                    else:
                        modes[c] = margs.pop()
                else:
                    margs.pop()
            elif neg:
                del modes[c]
            else:
                modes[c] = 1
        if len(margs):
            print "*** didn't decode mode args fully:", mstr, 'remaining', margs
        self.modes = modes

    def __repr__(self):
        key = self.key()
        if key:
            key = ' +k %s' % key
        return '<IrcChannel %s%s modes %s users: %s>' % (self.name, key, self.modes, ' '.join(self.users.keys()))

    __str__ = __repr__


STRING_OPTIONS = ('ircserver', 'ircport', 'ircuser', 'ircname', 'ircnick', 'irchost')
BOOLEAN_OPTIONS = ('autorejoin', 'usermsgs')
OPTIONS = STRING_OPTIONS + BOOLEAN_OPTIONS

class Client:
        
    def __init__(self, config, user, name, command):
	self.name = name
	if self.name == 'irc':
		self.name = 'IRC'
        self.channel = None
        self.user = user
        self.lastctxt = ""
        self.nicks = {}
        self.channels = {}
        self.autorejoin = 1
        self.usermsgs = 1
	self.drops = 0
	self.maxdrops = 3

	print "Options: ",config

        for opt, val in config.iteritems():
            if opt in OPTIONS:
                setattr(self, opt, val)

	if command:
	    splitup = command.split(' ',3)
	    if len(splitup) == 1 :
		self.ircserver = command
	    if len(splitup) == 2 :
		self.ircserver, self.ircport = splitup
	    if len(splitup) == 3 :
		self.ircserver, self.ircport, self.ircnick = splitup

        self.connect()

    def shutdown(self):
        try:
            self.channel.close()
            self.channel.handler = None
        except:
            pass
        print "<< IRC window cleared disconnect >>"
        self.channel = None

    def window_callback(self,name,win):
        print 'IRC window callback',name,win
        if name == '': return
        if name[0] in CHANNEL_LEADERS:
            win.maxdepth = 100
            return

        print "private message; expanding queue"
        win.maxdepth = 0

        return

    def nick_context(self, name):
        # if we have never seen this nick, send to unknown status window
        try:
            n = self.nicks[name]
        except:
            return ""

        # if this nick is on the channel we last chatted on, send there
        if n.channels.get(self.lastctxt):
            return self.lastctxt

        # otherwise grab the first channel this nick is on
        for c in n.channels:
            return c

        # shouldn't be able to happen...
        return ""

    def finduser(self, name):
        try:
            return self.nicks[name.lower()]
        except:
            return IrcUser(name,self.nicks)

    def findchannel(self, name):
        try:
            return self.channels[name.lower()]
        except:
            return IrcChannel(name,self.channels)

    def nick_rename(self, oldname, newname):
        #print "nick: %s -> %s" % (oldname, newname)
        self.finduser(oldname).rename(newname)

    def nick_join(self, name, chan):
        #print "nick: %s joins %s" % (name,chan)
        self.findchannel(chan).add(self.finduser(name))

    def nick_part(self, name, chan):
        #print "nick: %s leaves %s" % (name,chan)
        u = self.finduser(name)
        c = self.findchannel(chan)

        if name == self.ircnick:
            c.destroy()
            return

        c.remove(u)

    def nick_quit(self, name):
        #print "nick: %s quits" % name
        self.finduser(name).destroy()
        try:
            del self.nicks[name]
        except:
            pass

    def chan_nicks(self, chan, list):
        if not list: return
        names = list.split(' ')
        for n in names:
            if n:
                if n[0] in '@+':
                    self.nick_join(n[1:], chan)
                else:
                    self.nick_join(n, chan)

    def __getitem__(self, item):
        return getattr(self, item, None)

    def connect(self):
        if self.channel:
            self.ERROR('', 'Already connected to IRC server')
        else:
            self.lastctxt = ""
            self.INFO("Connecting to %s port %d" % (self.ircserver,self.ircport))
            self.channel = Channel(
                self,self.ircserver,self.ircport,'\r\n',self.irchost)

    def push(self, line):
        self.channel.push(line)

    def queue(self, tag, src, dst, txt):
        self.user.queue(Msg(self.name, tag, src, dst, txt))

    def REPLY(self, ctxt, text):
        self.queue("repl", "", ctxt, text)

    def ERROR(self, ctxt, text):
        self.queue("fail", "", ctxt, text)

    def INFO(self, text):
        self.queue("info", "", "", text)

    def SHOW(self, text):
        self.queue("fmsg", "", "", text)

    def DISP(self, ctxt, text):
        self.queue("info", "", ctxt, text)

    def SEND(self, tag, ctxt="", text=""):
        self.queue(tag, "", ctxt, text)

    def handle_close(self):
        print "<< IRC disconnect >>"
        self.channel.handler = None
        self.channel = None
        self.ERROR('', 'IRC server connection lost')
        if self.autorejoin and self.drops < self.maxdrops:
	    self.drops = self.drops + 1
            timesleft = self.maxdrops - self.drops
            self.INFO("Reconnecting, %d attempt%s left" % (timesleft, ('s', '')[timesleft == 1]))
            self.connect()

    def handle_connect(self):
        print "<< IRC connect >>"
        self.push('USER %(ircuser)s xxx xxx :%(ircname)s\n' % self)
        self.push('NICK %(ircnick)s\n' % self)
        self.INFO("Connection established.")

    def handle_line(self, data):
        # print 'line |%s|' % data
        if data[0] == ':':
            n = data.find(' ')
            if n == -1: return # bogus
            prefix = data[1:n]
            data = data[n+1:]

            n = prefix.find('!')
            if n != -1:
                prefix = prefix[:n]
        else:
            prefix = ''

        n = data.find(' :')
        if n == -1:
            args = data.split(' ')
        else:
            args = data[:n].split(' ')
            args.append(data[n+2:])

        try:
            getattr(self, 'irc_'+args[0],self.unknown)(prefix,args)
        except:
            print_traceback()

    def irc_PING(self, pref, args):
        self.push('PONG :%s\n' % args[1])

    def irc_PRIVMSG(self, pref, args):
        dst = args[1]
        text = args[2]
        if dst[0] in CHANNEL_LEADERS:
            tochan = 1
        else:
            tochan = 0

        if text[0] == '\01':
            l = len(text)
            text = text[1:l-1]
            n = text.find(' ')
            if n == -1: return
            kind = text[:n]
            text = text[n+1:]
            if kind == 'ACTION':
                if tochan:
                    tag = 'dmsg/act'
                else:
                    tag = 'smsg/act'
            else:
                return
        else:
            if tochan:
                tag = 'dmsg'
            else:
                tag = 'smsg'

        self.queue(tag, pref, dst, text)

    def irc_NOTICE(self, pref, args):
        dst = args[1]
        text = args[2]
        if dst[0] in CHANNEL_LEADERS:
            ctxt = dst
        elif pref == '':
            ctxt = ''
        else:
            ctxt = pref

        if text[0] == '\01':
            text = text[1:-1]
            n = text.find(' ')
            if n == -1: return
            kind = text[:n]
            text = text[n+1:]
            self.user.queue(Msg(self.name,'info',pref,ctxt,'*** CTCP %s reply from %s: %s' % (kind, pref, text)))
        else:
            self.user.queue(Msg(self.name,'info',pref,ctxt,'-%s- %s' % (pref, text)))

    def irc_NICK(self, pref, args):
        if pref == self.ircnick:
            self.ircnick = args[1]
            ctxt = self.lastctxt
        else:
            ctxt = self.nick_context(pref)
        self.nick_rename(pref, args[1])

        self.REPLY(ctxt,'%s is now known as %s' % (pref, args[1]))

    def irc_JOIN(self, pref, args):
        if pref == self.ircnick:
            self.user.queue(Msg(self.name,'show','',args[1],''))
        self.nick_join(pref, args[1])
        if self.usermsgs:
            self.REPLY(args[1], "%s has joined %s" % (pref,args[1]))

    def irc_PART(self, pref, args):
        self.nick_part(pref, args[1])
        print self.user.checkwindow(self.name,args[1])
        print args[1]
        if self.usermsgs and self.user.checkwindow(self.name,args[1]) :
            self.REPLY(args[1], "%s has left %s" % (pref, args[1]))

    def irc_KICK(self, pref, args):
        self.nick_part(args[2], args[1])
        self.REPLY(args[1], "%s has been kicked off of channel %s by %s (%s)" % (args[2], args[1], pref, args[3]))

    def irc_QUIT(self, pref, args):
        if self.usermsgs:
            self.REPLY(self.nick_context(pref), "%s has quit the network (%s)" % (pref,args[1]))
        self.nick_quit(pref)

        # MODE <channel> 
    def irc_MODE(self, pref, args):
        target = args[1]
        modestr = ' '.join(args[2:])
        if pref == target:
            self.REPLY(self.lastctxt, "%s set user mode %s" % (pref, modestr))
        else:
            if self.usermsgs or '.' in args[1]: # server-set mode
                self.REPLY(args[1], "%s set mode on %s: %s" % (pref, target, modestr))
            self.findchannel(target).modestr(modestr)

    def irc_376(self, pref, args):
        # '376' 'end of /MOTD command.
        self.drops = 0
        if self.autorejoin:
            self.INFO("Rejoining channels...")
            for n, c in self.channels.iteritems():
                try:
                    self.user.queue(Msg(self.name,'show','',c.name,''))
                    self.nick_join(self.ircnick, c.name)
                    self.push('join %s %s\n' % c.name, c.key())
                except:
                    pass
            else:
                self.INFO('No channels to rejoin')

    def irc_353(self, pref, args):
        # '353' '<yournick>' '@'|'=' '<channel>' '[@+]<name>...'
        chan = args[3].lower()
        nicks = ' '.join(args[4:])
        if self.channels.has_key(chan):
            self.chan_nicks(chan, nicks)
            dst = chan
        else:
            dst = ''
        self.DISP(dst, 'Users on %s: %s' % (chan, nicks))

        # 366 <nick> <channel> :End of /NAMES list.
    def irc_366(self, pref, args):
        channel = args[2]
        # in an ideal world, you print out the whole channel list
        # at the end, but really why bother?
        self.push('MODE %s\n' % channel)

        #311 <me> <nick> <user> <host> * :<real name>
        #312 <me> <nick> <server> :<server info>
        #313 <me> <nick> :is an irc operator
        #317 <me> <nick> <integer> :seconds idle
        #318 <me> <nick> :End of /WHOIS list
        #319 <me> <nick> :{[@|+]<channel><space>}
    def irc_311(self, pref, args):
        self.DISP(
            "% "+args[2],
            "%s@%s (%s)" % (args[3], args[4], args[6])
            )
    def irc_312(self, pref, args):
        self.DISP(
            "% "+args[2],
            "server: %s (%s)." % (args[3], args[4])
            )
    def irc_313(self, pref, args):
        self.DISP(
            "% "+args[2],
            "an irc operator."
            )
    def irc_317(self, pref, args):
        t = int(args[3])
        if t < 121:
            self.DISP(
                "% "+args[2],
                "idle: %d seconds" % t
                )
        else:
            t = int(t/60)
            self.DISP(
                "% "+args[2],
                "idle: %d minutes" % t
                )
    def irc_319(self, pref, args):
        self.DISP(
            "% "+args[2],
            "channels: %s" % args[3]
            )
    def irc_318(self, pref, args):
        self.user.queue(Msg(self.name,'show','',"% "+args[2],''))

        # 324 <me> <chan> <modes>
    def irc_324(self, pref, args):
        chan = args[2]
        modestr = ' '.join(args[3:])
        self.findchannel(chan).modestr(modestr)
        self.DISP(chan, 'Mode for %s is %s' % (chan, modestr))
        
        # 329 <me> <chan> <timestamp>
    def irc_329(self, pref, args):
        pass # don't care about channel ts

        # 332 <me> <chan> <topic>
        # 333 <me> <chan> <nick> <timestamp>
    def irc_332(self, pref, args):
        chan, topic = args[2:]
        self.DISP(chan, 'Topic: %s' % topic)
    def irc_333(self, pref, args):
        chan, nick, ts = args[2:]
        ts = time.strftime('%X on %x',time.localtime(int(ts)))
        self.DISP(chan, 'Topic set by %s at %s' % (nick, ts))

        # <nick> TOPIC <chan> <topic>
    def irc_TOPIC(self, pref, args):
        chan, topic = args[1:]
        if topic:
            self.DISP(chan, 'Topic set by %s: %s' % (pref, topic))
        else:
            self.DISP(chan, 'Topic unset by %s' % pref)

        # <nick> ERROR <error>
    def irc_ERROR(self, pref, args):
        self.ERROR('', args[1])

    def unknown(self, pref, args):
        try:
            n = int(args[0])
            del args[1] # discard the 'target'

            if (n <= 5) or n in (250, 251, 252, 254, 255, 265, 266, 372, 375):
                # MOTD and related information
                self.SHOW(' '.join(args[1:]))
                return
            elif (n >= 400) and (n < 500):
                # errors
                self.ERROR(self.lastctxt,' '.join(args[1:]))
                return
            self.INFO(' '.join(args))
            return
        except:
            pass
        self.INFO(pref + '> ' + repr(args))

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

    def cmd_IRC(self, tag, ctxt, args):
        self.ERROR('','IRC already running')

    def cmd_CONNECT(self, tag, ctxt, args):
        self.connect()

    def cmd_DISCONNECT(self, tag, ctxt, args):
        self.shutdown()

    def cmd_WHOIS(self, tag, ctxt, args):
        self.push('whois %s\n' % args)

    def cmd_KICK(self, tag, ctxt, args):
        n = args.find(' ')
        if n == -1:
            self.push('kick %s %s\n' % (ctxt, args))
        else:
            self.push('kick %s %s :%s\n' % (ctxt, args[:n], args[n+1:]))

    def cmd_JOIN(self, tag, ctxt, args):
        self.push('join %s\n' % args)

    def cmd_PART(self, tag, ctxt, args):
        if not args:
            args = ctxt
        self.push('part %s\n' % args)

    cmd_LEAVE = cmd_PART

    def cmd_ME(self, tag, ctxt, args):
        self.push('privmsg %s :\01ACTION %s\01\n' % (ctxt,args))
        self.user.queue(Msg(self.name,'dmsg/act',self.ircnick,ctxt,args))

    def cmd_SEND(self, tag, ctxt, args):
        self.push('privmsg %s :%s\n' % (ctxt,args))
        self.user.queue(Msg(self.name,'dmsg',self.ircnick,ctxt,args))

    def cmd_MSG(self, tag, ctxt, args):
        target, text = self.unpack2(args)
        self.push('privmsg %s :%s\n' % (target,text))
        self.user.queue(Msg(self.name,'dmsg',self.ircnick,target,text))

    def cmd_QUERY(self, tag, ctxt, args):
	target, tex = self.unpack2(args)
	self.user.queue(Msg(self.name,'info','',target,'Query to %s initiated' % target));
        self.user.queue(Msg(self.name,'show','',target,''))

    def cmd_NICK(self, tag, ctxt, args):
        self.push('nick %s\n' % args)

    def cmd_TOPIC(self, tag, ctxt, args):
        self.push('topic %s :%s\n' % (ctxt, args))

    def cmd_SET(self, tag, ctxt, args):
        opt, val = self.unpack2(args)
        opt = opt.lower()
        if len(opt) == 0:
            opts = list(OPTIONS)
            opts.sort()
            for opt in opts:
                val = getattr(self, opt)
                if opt in BOOLEAN_OPTIONS:
                    self.INFO("'%s' is %s" % (opt, ('unset', 'set')[val]))
                else:
                    self.INFO("%s = '%s'" % (opt, val))
        elif opt in STRING_OPTIONS:
            setattr(self, opt, val)
            self.INFO("Set '%s' to '%s'" % (opt, val))
        elif opt in BOOLEAN_OPTIONS:
            setattr(self, opt, boolean_from_input(getattr(self, opt), val))
            self.INFO("%s '%s'" % (('unset', 'set')[val], opt))
        else:
            self.ERROR(ctxt, "Cannot set '%s'" % opt)

    def cmd_DEBUG(self, tag, ctxt, args):
        for n in self.nicks:
            t = "user(%s): " % n
            n = self.nicks[n]
            for c in n.channels:
                t = t + c + " "
            print t

        for c in self.channels:
            t = "chan(%s): " % c
            c = self.channels[c]
            for n in c.users:
                t = t + n + " "
            print t

    def cmd_CLEAR(self, tag, ctxt, args):
        self.lastctxt = ''
        if ctxt[0] in CHANNEL_LEADERS:
            self.cmd_PART(tag, ctxt, args)

    def unpack2(self, args):
        n = args.find(' ')
        if n == -1:
            return args, ''
        else:
            return args[:n], args[n+1:]

class Channel (asynchat.async_chat):
    def __init__(self, handler, host, port, terminator, localaddr):
        asynchat.async_chat.__init__(self)
        self.set_terminator(terminator)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
	
	if (localaddr != '') :
		print "IRC Connection Local Address:",  localaddr

  		for res in socket.getaddrinfo(localaddr, None):
          		af, socktype, proto, canonname, sa = res
		self.bind(sa);
	else:
		print "localaddr not set"
	
        self.handler = handler
        self.buffer = ''
        handler.channel = self
	try:
            self.connect((host,port))
	except:
	    pass;

    def handle_connect(self):
        self.handler.handle_connect()

    def handle_close(self):
        if self.handler:
            self.handler.handle_close()
            self.producer_fifo.push(None)
        #else:
        #   print "<< huh? already closed. >>"

    def handle_expt (self) :
	pass

    def handle_error (self) :
	pass

    def found_terminator(self):
        try:
          self.handler.handle_line(self.buffer)
        except:
            print_traceback()
        self.buffer = ''

    def collect_incoming_data(self, data):
        self.buffer = self.buffer + data

def go():
    irc = IrcClient()
    irc.connect()
    asyncore.loop()
