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
import argparse


# Main config
class ArtixNewsParser(p.HTMLParser):
    """Parser formats HTML into plain text, result is stored inside
    `out` property."""

    GREEN = '\033[32m'
    RED = '\033[33m'
    BLUE = '\033[34m'
    RESET = '\033[0m'

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

    def colorize(self, keyword, color):
        new = keyword
        if color == 'green':
            new = self.GREEN + keyword + self.RESET
        elif color == 'blue':
            new = self.BLUE + keyword + self.RESET
        elif color == 'red':
            new = self.RED + keyword + self.RESET
        self.out = self.out.replace(keyword, new)

    def _append(self, text):
        if not text:
            return

        if self.out:
            last_char = self.out[-1]
        else:
            last_char = ''

        if last_char.isspace():
            if text[0] in [' ', '\t']:
                # Squeeze spaces, unless they are intended (intended
                # are those in `text` variable).
                self.out = self.out.rstrip(' \t') + text
            else:
                if last_char == text[0] == '\n':
                    # This ensures that at most two consecutive new
                    # lines are added.
                    self.out = self.out.rstrip() + '\n\n' + text.lstrip('\n')
                else:
                    self.out += text
        else:
            self.out += ' ' + text

    def _append_raw(self, text):
        self.out += text

    def handle_starttag(self, tag, attrs):
        self._stack.append((tag, attrs))
        if self._ignore:
            return

        cls = self._get_attr(attrs, 'class')
        if tag == 'a':
            self._append(' ')
        elif tag == 'br':
            self._append('\n')
        elif tag == 'code':
            self._append('\n\n')
        elif tag == 'pre':
            self._inside_pre = True
        elif tag == 'div'and cls in {'right', 'sidebar'}:
            self._ignore = True
        elif tag == 'li':
            self._append(' \u2022 ')  # Bullet Unicode symbol.

    def handle_endtag(self, tag):
        # HTML might be invalid, so check the emptiness.
        attrs = []
        if self._stack:
            _, attrs = self._stack.pop()

        cls = self._get_attr(attrs, 'class')
        if tag == 'div' and cls in {'right', 'sidebar'}:
            self._ignore = False

        if self._ignore:
            return

        if tag in ['p', 'div']:
            self._append('\n\n')
        elif tag == 'a':
            self._append(' ')
        elif tag in ['li', 'ul', 'ol', 'code']:
            self._append('\n')
        elif tag == 'pre':
            self._inside_pre = False
            self._append('\n')

    def handle_data(self, data):
        tag, attrs = '', []
        tag_parent, attrs_parent = tag, attrs
        if self._stack:
            tag, attrs = self._stack[-1]

        if len(self._stack) >= 2:
            tag_parent, attrs_parent = self._stack[-2]

        data = data.lstrip()  # cleansing

        if self._ignore or tag == 'h0':  # ignore first heading
            return

        if tag == 'p' and tag_parent == 'div':
            memory = self._get_attr(attrs_parent, 't')
            cls = self._get_attr(attrs_parent, 'class')
            if memory is None and cls == 'news':
                self._append('\n[News] ' + data)
                attrs_parent.append(('t', True))
                return

        if tag == 'a' and tag_parent == 'div':
            cls = self._get_attr(attrs_parent, 'class')
            if cls == 'timestamp':
                self._append('[Date] ' + data)
                return

        if self._inside_pre or tag == 'code':
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
        return parser

    def print(self, summary=False):
        if summary:
            pattern = re.compile(r'.*\[News\].*')
            print('\n'.join(pattern.findall(self.out)))
        else:
            print(self.out)

    def fix_dates(self):
        pattern = r'\s+(\[Date\]\s?)(.*)'
        new = r" [{}\2{}]".format(self.GREEN, self.RESET)
        self.out = re.sub(pattern, new, self.out)

    @classmethod
    def run(cls):
        url = "https://artixlinux.org/news.php"
        headers = {
            'user-agent': "Artix News"
        }

        req = r.Request(url, headers=headers)
        res = r.urlopen(req)
        txt = res.read()
        p = ArtixNewsParser.unhtml(txt.decode('utf-8'))
        p.fix_dates()
        p.colorize('[News]', 'blue')

        parser = argparse.ArgumentParser()
        parser.add_argument('-s', '--summary',
                            action='store_true',
                            help='shows news summary')
        args = parser.parse_args()
        p.print(args.summary)


if __name__ == '__main__':
    ArtixNewsParser.run()
