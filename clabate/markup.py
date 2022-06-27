'''
MarkupTemplate, a template for XML/HTML markup.
Escaping and minification helpers.

:copyright: Copyright 2019-2022 AXY axy@declassed.art
:license: BSD, see LICENSE for details.
'''

import re
import string
from xml.sax import saxutils

from .core import Template, FormatterWithIndent
from .invoke import Invoke

# All third-party dependencies are optional.
# Do not minify if a particular minifier is not installed.

# CSS and JS minification is performed by rcssmin and rjsmin.
# For HTML I haven't found anything fast and simple yet -- Axy.

try:
    import rjsmin
    _rjsmin_available = True
except ImportError:
    _rjsmin_available = False

try:
    import rcssmin
    _rcssmin_available = True
except ImportError:
    _rcssmin_available = False

#-----------------------------------------------------------------------------------
# String formatting and escaping.
#
# Substitution values should be escaped only once so we track them
# using `Escaped` subclass.

class Escaped:
    '''
    This subclass indicates the string is already escaped.
    It is not instantiated directly, so it's not based on any class.
    '''
    pass

def preserve_type(value, original_value):
    '''
    If value is an instance of `str`, make sure it has the same type as `original_value`.
    '''
    if isinstance(original_value, str) and value is not original_value:
        value = type(original_value)(value)
    return value

def make_escaped(value):
    '''
    Make sure the `value` is a subclass of `Escaped`.
    '''
    if not isinstance(value, Escaped):
        value_type = type(value)
        escaped_type = type(f'Escaped_{value_type.__name__}', (Escaped, value_type), {})
        value = escaped_type(value)
    return value

class MarkupFormatterBase:
    '''
    A few overrides to build formatter subclasses for markup templates.

    Here we do the following basic things for markup:
      * invoke escape when necessary
      * preserve types of strings
    '''
    def __init__(self, template):
        self.__template__ = template

    def vformat(self, format_string, args, kwargs):
        '''
        Make return value same type as `format_string`,
        which can be a subclass of `str`, i.e. `Markup`.
        Also, mark the result as escaped.
        '''
        result = super().vformat(format_string, args, kwargs)
        return make_escaped(preserve_type(result, format_string))

    def parse(self, format_string):
        '''
        Wrapper to escape literal text.
        '''
        for literal_text, field_name, format_spec, conversion in super().parse(format_string):
            # Preserve the type of literal text and format_spec.
            literal_text = preserve_type(literal_text, format_string)
            format_spec = preserve_type(format_spec, format_string)
            # Escape literal text. Don't escape format_spec because it will be processed recursively.
            literal_text = self.__template__.escape(literal_text)
            yield literal_text, field_name, format_spec, conversion

    def format_field(self, value, format_spec):
        '''
        Wrapper to escape substitutions.
        '''
        formatted_value = format(value, format_spec)
        return self.__template__.escape(preserve_type(formatted_value, value))

'''
`MarkupFormatter` is based on `FormatterWithIndent` to generate nicely looking markup.
'''
MarkupFormatter = type('MarkupFormatter', (MarkupFormatterBase, FormatterWithIndent), {})

'''
`LeanMarkupFormatter` is based on `string.Formatter` and is used in `MinifiedMarkupTemplate`
where indentation is unnecessary.
'''
LeanMarkupFormatter = type('LeanMarkupFormatter', (MarkupFormatterBase, string.Formatter), {})

class Escape(Invoke):
    '''
    This is a double-purpose class.
    First, as a callable it becomes `escape` method in `MarkupTemplate`.
    Second, it is based on `Invoke` and contains methods that can be used from templates.
    '''
    def attr(self, text, strip=True):
        '''
        Escape tag attribute.

        Example
        -------

        This snippet (yes, multiline attributes are okay):

            <p onclick={escape:attr("""
                do_this('asd');
                do_that("sdf");
            """)}>Click me!</p>

        Produces the following result:

            <p onclick="do_this('asd');&#10;    do_that(&quot;sdf&quot;);">Click me!</p>

        Args:
            text: attribute value
            strip: strip leading and trailing spaces (default: True)

        Returns:
            an instance of `Escaped` object
        '''
        if strip:
            text = text.strip()
        return make_escaped(saxutils.quoteattr(text))

    def markup(self, text):
        '''
        Do not escape `text`.

        This method is intended to keep markup in a non-markup string.

        Args:
            text: contains markup

        Returns:
            an instance of `Escaped` object
        '''
        # `text`, which actually is a part of format specification, is already escaped
        # because of recursive nature of `string.Formatter.vformat` method.
        # That's why we need to unescape it.
        return make_escaped(saxutils.unescape(text))

    def __call__(self, value):
        '''
        Escape `value`.

        Value can be a bare string or an instance of `Markup` class.

        Args:
            value: value to escape

        Returns:
            an instance of `Escaped` object for strings or value as is for all other types
        '''
        if not isinstance(value, str):
            # don't escape anything but strings
            return value
        if isinstance(value, Escaped):
            # already escaped
            return value
        if isinstance(value, Markup):
            # return markup as is, just mark it as escaped for consistency
            return make_escaped(value)
        # escape value
        return make_escaped(saxutils.escape(value))

class Markup(str):
    '''
    Markup indicator for raw XML/HTML code with helper methods.

    XXX probably this class should proxy `str` methods and make resulting strings `Markup` again?
        In some cases it would be helpful.
    '''
    @classmethod
    def join(self, separator, iterable):
        '''
        Join markup strings. Make sure all strings are either escaped or not escaped.
        '''
        num_escaped = 0
        num_not_escaped = 0
        strings = []
        for s in iterable:
            if isinstance(s, Escaped):
                num_escaped += 1
            else:
                num_not_escaped += 1
            strings.append(s)
        if not strings:
            return Markup('')
        if num_escaped and num_not_escaped:
            raise Exception('Cannot join escaped and not escaped markup.')
        result = separator.join(strings)
        if num_escaped:
            return make_escaped(result)
        else:
            return Markup(result)

    def __add__(self, other):
        '''
        Make concatenation easy.
        Not used in Clabate, it's just a helper for templates.
        However, more widely used .join should be wrapped with Markup anyway.
        '''
        if isinstance(other, Markup):
            return Markup(super().__add__(other))
        else:
            return NotImplemented

#-----------------------------------------------------------------------------------
# Markup templates.

class MarkupTemplateBase:
    '''
    A few extensions for `Template` class to implement XML/HTML escaping.
    '''
    def create_formatter(self):
        '''
        Override base method to create markup formatter.
        '''
        self._formatter = MarkupFormatter(self)

    escape = Escape()

    def get_missing_value(self, name, context):
        '''
        Escape values returned by property getters and `missing` method.
        '''
        value = super().get_missing_value(name, context)
        value = self.escape(value)
        # update cached value with escaped version
        context[name] = value
        return value

    @classmethod
    def dedent(self, text):
        '''
        Preserve type of dedented value.
        '''
        return preserve_type(super().dedent(text), text)

class MinifiedMarkupTemplateBase:
    '''
    A few overrides to produce minified markup.
    '''
    def create_formatter(self):
        '''
        Use lean formatter for a markup that will be minified.
        '''
        self._formatter = LeanMarkupFormatter(self)

    @classmethod
    def dedent(self, text):
        '''
        Do nothing.
        '''
        return text

    def format_string(self, s, context):
        formatted_str = super().format_string(s, context)
        minified_str = minify_markup(formatted_str)
        return preserve_type(minified_str, formatted_str)

'''
`MarkupTemplate` implements XML/HTML escaping.
'''
MarkupTemplate = type('MarkupTemplate', (MarkupTemplateBase, Template), {})

'''
`MinifiedMarkupTemplate` removes comments and unnecessary spaces from the resulting markup.
Spaces in <pre> tags are preserved.
'''
MinifiedMarkupTemplate = type('MinifiedMarkupTemplate',
                              (MinifiedMarkupTemplateBase, MarkupTemplateBase, Template), {})

_re_html_comments = re.compile('<!--.*?-->', flags=re.DOTALL)
_re_special_tags = re.compile(r'<(script|style|pre)(>| [^>]*>)(.*?)</\1>', flags=re.DOTALL)

def minify_markup(markup):
    '''
    Remove comments and unnecessary spaces from resulting markup.
    Preserve spaces in <pre> tags.

    This function can be used in a non-minified `MarkupTemplate` to minify parts of it:

        class MyTemplate(clabate.MarkupTemplate):

            html = minified("""
                <html>
                ...
                </html>
            """)

    Returns:
        Markup: minified markup
    '''
    # remove HTML comments
    markup = _re_html_comments.sub('', markup)
    # The following tags need special processing:
    # * script: use rjsmin
    # * style: use rcssmin
    # * pre: preserve spaces
    result = []
    start_index = 0
    for matchobj in _re_special_tags.finditer(markup):
        # process leading markup
        result.append(_minify_markup(markup[start_index:matchobj.start()]))
        # process opening tag: remove spaces
        result.append(
            _re_spaces.sub(' ', markup[matchobj.start():matchobj.start(3)])
        )
        # process inner content
        tag = matchobj.group(1)
        if tag == 'script':
            content = _minify_js(matchobj.group(3))
        elif tag == 'style':
            content = _minify_css(matchobj.group(3))
        else:
            content = matchobj.group(3)
        result.append(content)
        # append closing tag
        result.append(markup[matchobj.end(3):matchobj.end()])
        # bump start_index
        start_index = matchobj.end()
    # process ending markup
    result.append(_minify_markup(markup[start_index:]))
    return Markup.join('', result)

_re_spaces = re.compile(r'\s{2,}')

def _minify_markup(markup):
    # XXX I haven't found any good HTML minification library so far -- Axy
    # Simply remove unnecessary spaces.
    markup = _re_spaces.sub(' ', markup)
    return markup.strip()

def _minify_js(js):
    if _rjsmin_available:
        return rjsmin.jsmin(js)
    else:
        return js

def _minify_css(css):
    if _rcssmin_available:
        return rcssmin.cssmin(css)
    else:
        return css
