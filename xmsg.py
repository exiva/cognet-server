#!/usr/local/bin/python
# -*- python -*-
## $Id: xmsg.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

class Msg:
    def __init__(self, app, tag, src, dst, txt, serial=None):
        self.tag = tag
        self.src = src
        self.dst = dst
        self.app = app
        self.txt = txt
        self.serial = serial

    def send(self, session):
        if self.serial:
            sn = self.serial.__str__()
        else:
            sn = ''

        if self.app == '':
            line = session.mark.join((sn, self.tag, self.src, self.dst, self.txt))
        else:
            if self.tag == 'smsg':
                # need to rewrite message as fmsg
                line = session.mark.join((sn, 'fmsg', '', '%s %s' % (self.app, self.src),
                                          '<%s> %s' % (self.src, self.txt)))
            else:
                line = session.mark.join((sn, self.tag, self.src,
                                          '%s %s' % (self.app, self.dst), self.txt))
        session.push(line + '\n')

    def __repr__(self):
        return '<Msg: app|%s| tag|%s| src|%s| dst|%s| txt|%s|>' % (self.app, self.tag, self.src, self.dst, self.txt)

    __str__ = __repr__
