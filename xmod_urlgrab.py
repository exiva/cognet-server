#!/usr/local/bin/python
# -*- python -*-
## $Id: xmod_urlgrab.py,v 1.1.1.1 2004/09/29 19:13:08 rit Exp $

# Copyright (c) 2004 Brendan W. McAdams and the Cognet Contributors
# Copyright 2003 Brian J. Swetland
# Copyright 2003 Daniel Grobe Sachs
# Enhancements - Kenneth B. Foreman, Leigh L. Klotz Jr, Nicholas Riley, Brendan W. McAdams
# See LICENSE for redistribution terms

from xmsg import Msg
import copy, re, urllib

PAT_URL = re.compile(r''' #"
                 (?x)( # verbose identify URLs within text
((?i)http|https|mailto|phone) # make sure we find a resource type
                   :// # ...needs to be followed by colon-slash-slash
        (\w+[:.]?){2,} # at least two domain groups, e.g. (gnosis.)(cx)
                  (/?| # could be just the domain name (maybe w/ slash)
            [^ \n\r"]+ # or stuff then space, newline, tab, quote
                [\w/]) # resource name ends in alphanumeric or slash
   (?=[\s\.,>)'"\]]|$) # assert: followed by white or clause ending
                     ) # end of match group
                     ''')
			#" Emacs python-mode gets confused otherwise

# this really needs to be replaced by a regex that isn't designed for
# processing mail messages
PAT_EMAIL = re.compile(r'''
                (?xm)  # verbose identify URLs in text (and multiline)
             (?=^.{11} # Mail header matcher
     (?<!Message-ID:|  # rule out Message-ID's as best possible
         In-Reply-To)) # ...and also In-Reply-To
                (.*?)( # must grab to email to allow prior lookbehind
    ([A-Za-z0-9-]+\.)? # maybe an initial part: DAVID.mertz@gnosis.cx
         [A-Za-z0-9-]+ # definitely some local user: MERTZ@gnosis.cx
                     @ # ...needs an at sign in the middle
          (\w+\.?){2,} # at least two domain groups, e.g. (gnosis.)(cx)
   (?=[\s\.,>)'"\]]|$) # assert: followed by white or clause ending
                     ) # end of match group
                     ''')

PAT_PHONE = re.compile(r'(\+?[()0-9 \-]{7,20})')

# unescaped URLs OK
def extract_urls(s):
    urls = [u[0] for u in PAT_URL.findall(s)]
    urls.extend(['mailto:' + e[1] for e in PAT_EMAIL.findall(s)])
    for e in PAT_PHONE.findall(s):
        # if someone wants to make this check more efficient, be my guest
        if len(re.findall(r'\d', e)) in range(7, 20):
            urls.append('phone:' + e.strip())
    return urls

class Client:
    def __init__(self, config, user, name, command):
        self.user = user

    def command(self, tag, dst, txt):
        pass

    def shutdown(self):
        return

    def window_callback(self, name, win):
        return

    def input_hook(self, serial, tag, app, name, txt):
        return ( serial, tag, app, name, txt )

    def output_hook(self, msg):
        tag = msg.tag
        if tag in ('smsg', 'smsg/act'):
            dst = msg.src
        elif tag == 'url':
            return msg
        else:
            dst = msg.dst
        urls = extract_urls(msg.txt)
        for url in urls:
            scheme, loc = url.split(':', 1)
            scheme = scheme.lower()
            item = url
            if scheme in ('http', 'https'):
                src = 'Go To'
            if scheme == 'mailto':
                src = 'Email'
                item = loc
            elif scheme == 'phone':
                src = 'Phone'
                item = loc
            url = ':'.join((scheme, urllib.quote(loc, ';/?:@&=+$,#')))
            self.user.queue(Msg(msg.app, 'url', src, dst, url + ' ' + item))
        return msg
