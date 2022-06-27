'''
Pygments-based syntax highlighting helpers.

:copyright: Copyright 2019-2021 AXY axy@declassed.art
:license: BSD, see LICENSE for details.
'''

import textwrap

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

from ..invoke import Invoke
from ..markup import Markup

class Pygments(Invoke):
    '''
    Pygments class provides syntax highlighting methods
    '''
    def highlight(self, lexer_name, code,
                  dedent=True,
                  linenos=False,
                  lexer_options={},
                  filters=[],
                  formatter_options={}):
        '''
        Syntax highlighting.

        Args:
            dedent: dedent code, default: True
            linenos: shortcut for `formatter_options['linenos']`
            lexer_options: options passed to lexer
            filters: list of (filter_name, filter_options)
            formatter_options: options passed to formatter.

        Returns:
            an instance of `Markup` class
        '''
        if dedent:
            code = textwrap.dedent(code).strip('\r\n')

        lexer = get_lexer_by_name(lexer_name, **lexer_options)
        for filter_name, filter_options in filters:
            lexer.add_filter(filter_name, **filter_options)

        formatter_options = formatter_options.copy()
        formatter_options['linenos'] = linenos
        formatter = HtmlFormatter(**formatter_options)

        return Markup(highlight(code, lexer, formatter))

    def stylesheet(self, arg='.highlight'):
        '''
        Return stylesheet.
        '''
        return Markup(HtmlFormatter().get_style_defs(arg))

class PygmentsMixin:
    '''
    Highlighting mixin for templates.

    Usage::
        {pygments:highlight('python', """
            def main():
                print('Hello, world!')
        """)}
    '''
    pygments = Pygments()
