'''
Implementation of the basic Template class

:copyright: Copyright 2019-2022 AXY axy@declassed.art
:license: BSD, see LICENSE for details.
'''

from collections import defaultdict
import inspect
import string
from textwrap import dedent
import types

#-----------------------------------------------------------------------------------
# Helper classes and functions.

def depends_on(names):
    '''
    A decorator to give a hint that a property depends on other values.
    This might be necessary when a property getter uses formatted string
    from the rendering context:

        moo = '{foo}'
        bar = '{baz}'

        @property
        @depends_on('bar')
        def foo(self, context):
            return f'{context.bar}'

    Args:
        names: a list, a set, or a string with names separated by space
    '''
    if isinstance(names, str):
        names = names.split()

    def decorator(func):
        func.depends_on = names
        return func

    return decorator

class MissingValue:
    '''
    Mixin class for missing substitutions, constructed by _make_missing_value.
    For simple substitutions this mixin is unnecessary but for
    more or less complex substitutions, such as

        {foo.bar[1][value]}

    where missing value is treated by formatter as a dict or a list,
    it helps to identify missing things, allowing access to items,
    thus suppressing subsequent exceptions.

    This makes stack trace less cryptic, which would look like this:

        File "/usr/lib/python3.7/string.py", line 301, in get_field
            obj = getattr(obj, i)
        AttributeError: 'str' object has no attribute 'bar'
    '''
    def __getattr__(self, name):
        return self

    def __getitem__(self, name):
        return self

    def __format__(self, format_spec):
        '''
        This method is required when the missing substitution contains format specification.
        '''
        return self

def _make_missing_value(value):
    '''
    Add MissingValue to the type of value.

    Args:
        value: an instance of `str` or a subclass of `str`

    Returns:
        An instance of type(value) and `MissingValue`.
    '''
    value_type = type(value)
    missing_type = type(f'MissingValue_{value_type.__name__}', (MissingValue, value_type), {})
    return missing_type(value)

class Comment:
    '''
    Comment class provides `__format__` method to swallow comments.

    Example
    -------

    This snippet:

        The red dog
        {comment: or fox?}
        jumps over the lazy fox. {comment: at last, maybe it's
        a fox who jumps over the lazy dog?}

    Produces the following result:

        The red dog

        jumps over the lazy fox.
    '''

    def __format__(self, format_spec):
        '''
        Comment is in `format_spec`. Simply ignore it and return empty string.
        '''
        return ''

def escape_braces(text):
    '''
    Double all braces in the `text` to avoid processing them as substitutions.

    This helper is useful when a text contains lots of braces and no substitutions.
    '''
    return text.replace('{', '{{').replace('}', '}}')

def alter_braces(opening_brace, closing_brace, text):
    '''
    Use opening_brace and closing_brace for substitutions.
    For example,

        alter_braces('❰', '❱', """
            function my_javascript_code() {
                if(❰wow❱) {
                    alert('❰wow❱')
                }
            }
        """)
    '''
    return escape_braces(text).replace(opening_brace, '{').replace(closing_brace, '}')


#-----------------------------------------------------------------------------------
# Rendering context and keyword arguments.

class Context(dict):
    '''
    Rendering context for templates.
    '''
    def __init__(self, template):
        self.__template__ = template
        self.__kwargs_stack__ = []

    def __missing__(self, name):
        '''
        Call `get_missing_value` method of template.
        '''
        if self.__template__ is None:
            raise AttributeError(name)
        else:
            return self.__template__.get_missing_value(name, self)

    def _decouple(self):
        '''
        Decouple context from template when rendering is done.
        '''
        self.__template__ = None

    # XXX it's probably not a good idea to blend kwargs with context,
    # but other solutions lead to more cumbersome code

    def _push_kwargs(self, kwargs):
        '''
        Push keyword arguments passed to render_str on the stack.
        '''
        self.__kwargs_stack__.insert(0, kwargs)

    def _pop_kwargs(self):
        '''
        Pop keyword arguments from the stack.
        '''
        del self.__kwargs_stack__[0]

    def get(self, key, default):
        for kwargs in self.__kwargs_stack__:
            if key in kwargs:
                return kwargs[key]
        return super().get(key, default)

    def __getitem__(self, key):
        for kwargs in self.__kwargs_stack__:
            if key in kwargs:
                return kwargs[key]
        return super().__getitem__(key)

    def __contains__(self, key):
        for kwargs in self.__kwargs_stack__:
            if key in kwargs:
                return True
        return super().__contains__(key)

    def __getattr__(self, name):
        '''
        Let accessing the data using dot notation.
        '''
        if name in self:
            return self[name]
        else:
            return self.__missing__(name)

#-----------------------------------------------------------------------------------
# Formatters.

# need some parsers from this module:
import _string

class AnalysingFormatter(string.Formatter):
    '''
    This formatter finds template dependencies.
    '''
    def reset(self):
        self.dependencies = set()

    def get_field(self, field_name, args, kwargs):
        '''
        Collect dependencies.
        '''
        first, rest = _string.formatter_field_name_split(field_name)
        self.dependencies.add(first)
        return '', first

    def convert_field(self, value, conversion):
        '''
        Do nothing.
        '''
        return ''

    def format_field(self, value, format_spec):
        '''
        Do nothing.
        '''
        return ''

class FormatterWithIndent(string.Formatter):
    '''
    This formatter maintains proper indentation.
    '''
    def vformat(self, format_string, args, kwargs):
        '''
        Simplified version of the original vformat.
        '''
        return self._vformat(format_string, args, kwargs, 2)

    def _vformat(self, format_string, args, kwargs, recursion_depth):
        '''
        Maintain indentation and merge newlines after substitutions when necessary.
        Based on the original _vformat
        '''
        if recursion_depth < 0:
            raise ValueError('Max string recursion exceeded')

        # the ending line separator of last substitution is used to merge newlines
        subst_newline = ''

        result = []
        for literal_text, field_name, format_spec, conversion in self.parse(format_string):

            # split literal text into separate lines
            literal_lines = literal_text.splitlines(keepends=True)

            # merge newlines
            if literal_lines:
                if subst_newline:
                    # to avoid re-implementing newline separator detection logic,
                    # simply call .splitlines for the single line, without keepends
                    if literal_lines[0].splitlines()[0] == '':
                        literal_lines = literal_lines[1:]
                        subst_newline = ''

            # use spaces from the last literal line for indentation, except line separators
            indent = ''
            if literal_lines:
                if literal_lines[-1].isspace():
                    indent = literal_lines[-1].splitlines()[0]
                    # avoid double indentation
                    literal_lines[-1] = literal_lines[-1].replace(indent, '')

            # output the literal text
            if literal_lines:
                result.extend(literal_lines)

            # if there's a field, output it
            if field_name is not None:
                # this is some markup, find the object and do
                #  the formatting
                if field_name == '':
                    raise ValueError('Empty fields are not supported')
                if field_name.isdigit():
                    raise ValueError('Numbered fields are not supported')

                # given the field_name, find the object it references
                #  and the argument it came from
                obj, arg_used = self.get_field(field_name, args, kwargs)

                # do any conversion on the resulting object
                obj = self.convert_field(obj, conversion)

                # expand the format spec, if needed
                format_spec = self._vformat(format_spec, args, kwargs, recursion_depth - 1)

                # format the object
                formatted_value = self.format_field(obj, format_spec)
                formatted_lines = formatted_value.splitlines(keepends=True)

                # get the ending separator from the last formatted line
                if formatted_lines:
                    last_line = formatted_lines[-1]
                    last_line_without_separator = last_line.splitlines()[0]
                    subst_newline = last_line[len(last_line_without_separator):]

                    # output indented value
                    if indent:
                        for line in formatted_lines:
                            result.append(indent)
                            result.append(line)
                    else:
                        # no indentation
                        result.append(formatted_value)

        return ''.join(result)

#-----------------------------------------------------------------------------------
# Base template class

class Template:
    '''
    Base template class.
    '''

    def __init__(self, **kwargs):
        self.create_formatter()

        # Collect all attributes of template class.
        class_attributes = self._collect_class_attributes()

        # Group class atributes into:
        self._data_attributes = dict()  # object attributes other than strings
        self._properties = dict()       # object methods decorated with @property
        potential_templates = dict()    # object attributes of string types

        for k, v in class_attributes.items():
            if isinstance(v, str):
                # Attributes of `str` type are potential templates.
                potential_templates[k] = v
            else:
                # All other attributes are template attributes or template properties.
                if self._is_template_property(v):
                    self._properties[k] = v
                else:
                    self._data_attributes[k] = v

        # Set object attributes from kwargs. Strings can be templates.
        for k, v in kwargs.items():
            if isinstance(v, str):
                # kwargs of `str` type are potential templates.
                potential_templates[k] = v
            else:
                # All other kwargs.
                setattr(self, k, v)

        # Discover template dependencies.
        template_dependencies = self._collect_template_dependencies(potential_templates)

        # Find formatting order.
        format_order = self._find_formatting_order(template_dependencies)

        # Build `_template_attributes` list.
        # This list contain templates in the formatting order.
        # Each item is a tuple: (attribute name, dedented template string)
        self._template_attributes = []
        for attr_name in format_order:
            if attr_name in self._properties:
                # skip property dependencies
                continue
            dedented = self.dedent(potential_templates[attr_name])
            self._template_attributes.append((attr_name, dedented))
            del potential_templates[attr_name]

        # All remaining strings in `potential_templates` are actually not templates.
        # Format and append them either to `_data_attributes` or set as attributes of self if they come from kwargs.
        # Always format all these strings for consistency.
        # They may contain escaped braces {{...}} and no substitutions.
        # Also, such a formatting is important for markup templates, when escaping is involved.
        temp_context = Context(self)
        for attr_name, attr_value in potential_templates.items():
            dedented = self.dedent(attr_value)
            if attr_name in kwargs:
                setattr(self, attr_name, dedented)
            else:
                self._data_attributes[attr_name] = self._formatter.vformat(dedented, tuple(), temp_context)

    def create_formatter(self):
        '''
        Create formatter and set `self._formatter` attribute.
        '''
        self._formatter = FormatterWithIndent()

    def _is_template_property(self, attr):
        '''
        Check if `attr` is a special property with additional `context` argument.
        '''
        if isinstance(attr, property):
            argspec = inspect.getfullargspec(attr.fget)
            if len(argspec.args) > 1 or \
               (len(argspec.args) == 1 and len(argspec.kwonlyargs) > 0):
                return True
        return False

    def _collect_class_attributes(self):
        '''
        Collect class attributes including all base classes
        in the hierarchy except object and this, Template class.
        '''
        class_attributes = dict()
        # Reverse method resolution order and exclude first two entries: base `object` class and self:
        reverse_mro = inspect.getmro(self.__class__)[-2::-1]
        for template_class in reverse_mro:
            for k, v in vars(template_class).items():
                # Exclude private attributes.
                if k.startswith('_'):
                    continue
                # Exclude methods
                if isinstance(v, (types.FunctionType, classmethod)):
                    continue
                class_attributes[k] = v
        return class_attributes

    def _collect_template_dependencies(self, potential_templates):
        '''
        Use `AnalysingFormatter` to parse strings and find their dependencies.

        Args:
            potential_templates (dict): attribute names and their values.

        Returns:
            dict: keys are attribute names which are templates,
                  values are names of substtutions they depend on.
        '''
        formatter = AnalysingFormatter()
        template_dependencies = defaultdict(set)
        for template_attr_name, template_string in potential_templates.items():
            formatter.reset()
            formatter.format(template_string)
            for name in formatter.dependencies:
                template_dependencies[template_attr_name].add(name)
                # if name refers to a property, check depends_on
                if name in self._properties:
                    prop = self._properties[name]
                    depends_on = getattr(prop.fget, 'depends_on', [])
                    for prop_dependency in depends_on:
                        template_dependencies[name].add(prop_dependency)
        return template_dependencies

    def _find_formatting_order(self, template_dependencies):
        '''
        Find out formatting order for template strings.
        '''
        # Build dependency graph.
        dependency_graph = defaultdict(list)
        for template_attr_name, others in template_dependencies.items():
            for other in others:
                dependency_graph[template_attr_name].append(other)
                dependency_graph[other] = dependency_graph[other]

        # Topological sort.
        # Cycles are not detected!
        format_order = []

        visited = dict((node_name, False) for node_name in dependency_graph)

        def sort_visit(node_name):
            visited[node_name] = True
            for other in dependency_graph[node_name]:
                if not visited[other]:
                    sort_visit(other)
            format_order.append(node_name)

        for node_name in dependency_graph:
            if not visited[node_name]:
                sort_visit(node_name)

        # Filter format order by real templates.
        return list(filter(lambda name: name in template_dependencies, format_order))

    def get_missing_value(self, name, context):
        '''
        Try to get a value for `name`.
        This method is invoked indirectly from __missing__ handler of rendering context.
        '''
        if name in self._properties:
            # call property getter
            value = self._properties[name].fget(self, context)
        else:
            # call missing method
            value = self.missing(name)
            value = _make_missing_value(value)
        # cache value
        context[name] = value
        return value

    @classmethod
    def dedent(self, text):
        '''
        Amended version of `textwrap.dedent`.
        Remove leading newline.
        '''
        text = dedent(text)
        lines = text.splitlines(keepends=True)
        if lines and lines[0].splitlines()[0] == '':
            lines = lines[1:]
        return ''.join(lines)

    def render(self, **kwargs):
        '''
        Render self.

        Collect all properties and attributes into a rendering context dict and then
        format all template strings defined as class attributes.
        '''
        # prepare rendering context
        context = self._prepare_context(**kwargs)

        # render template attributes
        for attr_name, template_string in self._template_attributes:
            if attr_name in context:
                # skip already formatted value,
                # or a value that might be set when context was populated
                continue
            context[attr_name] = self.format_string(template_string, context)

        # decouple rendering context from template
        # to avoid invocation of __missing__ handler from the caller's code
        context._decouple()

        return context

    def render_str(self, context, s, **kwargs):
        '''
        Render template string `s` in the `context`.

        Returns:
            str: formatted template string
        '''
        context._push_kwargs(kwargs)
        try:
            return self.format_string(s, context)
        finally:
            context._pop_kwargs()

    def _prepare_context(self, **kwargs):
        '''
        Prepare rendering context.

        Returns:
            an instance of Context class
        '''
        context = Context(self)

        # populate context with data attributes
        # XXX is it good to blend everything in the context?
        context.update(self._data_attributes)

        # populate context with variables passed to `__init__` or set in any other way for `self`:
        for k, v in vars(self).items():
            # exclude private attributes
            if k.startswith('_'):
                continue
            context[k] = v

        # populate context with kwargs
        context.update(kwargs)

        return context

    def format_string(self, s, context):
        '''
        Invoke formatter.
        '''
        return self._formatter.vformat(s, tuple(), context)

    def missing(self, name):
        '''
        Handler for missing template data.

        Args:
            name: name of an attribute, missing from the rendering context.
        '''
        raise AttributeError(f'{self.__class__.__name__} does not provide {name}')

    comment = Comment()

#-----------------------------------------------------------------------------------
# Lean template class

class LeanTemplate(Template):
    '''
    `LeanTemplate` uses `string.Formatter`.
    It can be used for cases when indentation is unnecessary.
    Or, for those who concerned about performance.
    '''
    def create_formatter(self):
        '''
        Create formatter and set `self._formatter` attribute.
        '''
        self._formatter = string.Formatter()

    @classmethod
    def dedent(self, text):
        '''
        Do nothing.
        '''
        return text
