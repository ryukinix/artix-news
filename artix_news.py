#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#    Copyright © 2019 Manoel Vilela
#
#    @project: Artix News
#     @author: Manoel Vilela
#      @email: manoel_vilela@engineer.com
#
# NOTE: Based heavily in: arch:
# https://github.com/mjiricka/archnews/blob/master/archnews

import html.parser as p
import urllib.request as r
import re


# Main config
class ArtixNewsParser(p.HTMLParser):
    """Parser formats HTML into plain text, result is stored inside
    `out` property."""

    def __init__(self):
        super().__init__()

        self.out = ''
        self._stack = []
        self._inside_pre = False
        self._ignore = False

    @staticmethod
    def _squeeze_whitespace(text):
        """Squeezes whitespaces into one single space."""
        return re.sub(r'\s+', ' ', text)

    @staticmethod
    def _get_attr(attrs, key):
        value = None
        for k, v in attrs:
            if k == key:
                value = v
                break
        return value

    def _append(self, text):
        if not text:
            return

        if self.out:
            last_char = self.out[-1]
        else:
            last_char = ''

        if last_char.isspace():
            if text[0] in [' ', '\t']:
                # Squeeze spaces, unless they are intended (intended are those in
                # `text` variable).
                self.out = self.out.rstrip(' \t') + text
            else:
                if last_char == text[0] == '\n':
                    # This ensures that at most two consecutive new lines are added.
                    self.out = self.out.rstrip() + '\n\n' + text.lstrip('\n')
                else:
                    self.out += text
        else:
            self.out += text

    def _append_raw(self, text):
        self.out += text

    def handle_starttag(self, tag, attrs):
        self._stack.append((tag, attrs))
        if self._ignore:
            return

        if  tag == 'a':
            self._append('<')
        elif tag == 'br':
            self._append('\n')
        elif tag == 'code':
            self._append('\n\n')
        elif tag == 'pre':
            self._inside_pre = True
        elif tag == 'div' and self._get_attr(attrs, 'class') in {'right', 'sidebar'}:
            self._ignore = True
        elif tag == 'li':
            self._append(' \u2022 ')  # Bullet Unicode symbol.

    def handle_endtag(self, tag):
        # HTML might be invalid, so check the emptiness.
        attrs = []
        if self._stack:
            _, attrs = self._stack.pop()

        if tag == 'div' and self._get_attr(attrs, 'class') in {'right', 'sidebar'}:
            self._ignore = False

        if self._ignore:
            return

        if tag in ['p', 'div']:
            self._append('\n\n')
        elif tag == 'a':
            self._append('>')
        elif tag in ['li', 'ul', 'ol', 'code']:
            self._append('\n')
        elif tag == 'pre':
            self._inside_pre = False
            self._append('\n')

    def handle_data(self, data):
        if self._stack:
            tag, attrs = self._stack[-1]
        else:
            tag = ''

        data = data.lstrip()

        if self._ignore or tag == 'h0':
            return

        # if tag == 'p' and len(self._stack) >= 2:
        #     _, attrs_parent = self._stack[-2]
        #     if self._get_attr(attrs_parent, 'class') == 'news':
        #         self._append_raw('\n[News] ' + data)

        elif self._inside_pre or tag == 'code':
            # Everything inside <pre> or in code is indented by three spaces.
            indented_data = '\n'.join(['\t'+line for line in data.split('\n')])
            self._append_raw(indented_data)
        elif tag == 'pre':
            self._append('\n')
        elif tag == 'script':
            pass
        else:
            squeezed_data = self._squeeze_whitespace(data)
            # Do not allow spaces at a paragraph beginning.
            if squeezed_data != ' ' or (self.out and self.out[-1] != '\n'):
                self._append(squeezed_data)

    def error(self, message):
        raise SyntaxError('Error when parsing message: ' + message)

    @classmethod
    def unhtml(cls, text):
        """Uses parser on given `text` and returns the result."""
        parser = cls()
        parser.feed(text)
        return parser.out



url = "https://artixlinux.org/news.php"
headers = {
    'user-agent': "Chrome/72.0.3626.109"
}


req = r.Request(url, headers=headers)
res = r.urlopen(req)
txt = res.read()
print(ArtixNewsParser.unhtml(txt.decode('utf-8')))
