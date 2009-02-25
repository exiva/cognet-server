#!/usr/local/bin/python
# -*- python -*-
## $Id: xmod_rpn.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

from xmsg import Msg
from xtools import print_traceback

def makenum(instr) :
    try:
        num = float(instr)
    except ValueError:
        num = None

    return num

class Stack:
    def __init__(self) :
        self.data = {}
        self.length = 0

    def pop(self) :
        if self.length == 0 :
            raise "EmptyStack"

        out = self.data[self.length-1]
        del self.data[self.length-1]
        self.length -= 1
        return out

    def push(self, elem) :
        self.data[self.length] = elem
        self.length += 1

    def size(self) :
        return self.length

    def get(self, num) :
        return self.data[num]

    def set(self, num, elem) :
        self.data[num] = elem

class Client:
    def __init__(self, config, user, name, command):
        self.user = user;
	self.name = name;
        self.stack = Stack();
        self.command('send','%server',command)
        self.user.queue( Msg(self.name, 'fail', '', '', 'RPN started') )

    def command(self, tag, dst, txt):
        if( tag != 'send' ):
            return

        ops = txt.split(" ")

        try : 
            for i in ops :
                self.op(i)
        
            self.makedisplay()
        except "StackEmpty":
            self.user.queue( Msg(self.name,'fail','','','Empty stack error') )

        except :
            print_traceback()
            self.user.queue( Msg(self.name,'fail','','','Unhandled exception') )
            

    def shutdown(self):
        return

    def window_callback(self, name, win):
        return

    def input_hook(self, serial, tag, app, name, txt):
        return ( serial, tag, app, name, txt )

    def output_hook(self, msg):
        return msg

    def makedisplay(self) :
        self.user.queue(Msg(self.name, 'clear', '', '', ''))

        if self.stack.size() == 0 :
            self.user.queue(Msg(self.name,'repl','','','Empty stack'))
            return

        for i in range(0,self.stack.size()) :
            self.user.queue(Msg(self.name,'repl','','',     \
                str(self.stack.size()-i-1) + ': ' +     \
                str(self.stack.get(i))))
    def op(self,txt) :

        if( makenum(txt) ):
            self.stack.push( makenum(txt) )
            return
 
        if( (txt == '+') | (txt == 'a') ) :
            self.stack.push(
                self.stack.pop() +
                self.stack.pop() 
            )
            return

        if( (txt == '-') | (txt == 's') ) :
            self.stack.push(
                -self.stack.pop() +
                self.stack.pop() 
            )
            return

        if( (txt == '*') | (txt == 'm') ) :
            self.stack.push(
                self.stack.pop() *
                self.stack.pop() 
            )
            return

        if( (txt == '/') | (txt == 'd') ) :
            self.stack.push(
                (1.0/self.stack.pop()) *
                self.stack.pop() 
            )
            return

        if( txt == 'c' ) :
            self.stack = Stack()
