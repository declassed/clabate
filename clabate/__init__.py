'''
Clabate: class based templates.

This minimalistic template system utilizes python class hierarchy,
class attributes, and string formatting.

:copyright: Copyright 2019-2022 AXY axy@declassed.art
:license: BSD, see LICENSE for details.

'''

__version__ = '0.4.1'

# shortcut imports
from .core import (
    Template, LeanTemplate,
    alter_braces, escape_braces
)
from .markup import (
    MarkupTemplate, MinifiedMarkupTemplate, Markup, Escaped,
    make_escaped, minify_markup
)
