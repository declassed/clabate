'''
Basic examples.

:copyright: Copyright 2021-2022 AXY axy@declassed.art
:license: BSD, see LICENSE for details.
'''

import time
from types import SimpleNamespace

from .. import Template, LeanTemplate, escape_braces, depends_on

#-----------------------------------------------------------------------------------
# Inheritance

class Fruit(Template):
    '''
    This is an abstract template for fruits.
    Some substitutions are not defined yet.
    '''
    snippet = 'This is {article} {fruit_name}. The {fruit_name} is {fruit_attribute}.'

    # Clabate relies on string formatting only and does not offer
    # any mini language for templates.
    # To build substitutions dynamically, you can use class properties.
    @property
    def article(self, context):
        # Simplified logic just for illistration:
        if context.fruit_name.lower()[0] in 'bcdfghjklmnpqrstuvwxyz':
            return 'a'
        else:
            return 'an'

def fruit_example():
    # rendering must fail because some substitutions are missing
    template = Fruit()
    try:
        context = template.render()
        print(context.snippet)
        assert False, 'WTF? Fruit should fail!'
    except AttributeError as e:
        assert any(s in e.args[0] for s in [
            'Fruit does not provide fruit_name',
            'Fruit does not provide fruit_attribute'
        ])

class Apple(Fruit):
    '''
    Let's provide missing substitutions.
    '''
    fruit_name = 'apple'
    fruit_attribute = 'pretty {fruit_color}'
    # the missing fruit_color will be provided via render()

def apple_example():
    template = Apple()
    context = template.render(fruit_color='red')
    expected_result = 'This is an apple. The apple is pretty red.'
    assert context.snippet == expected_result
    # note that strings passed as arguments to the render method are not formatted:
    context = template.render(fruit_color='{red}')
    expected_result = 'This is an apple. The apple is pretty {red}.'
    assert context.snippet == expected_result

class Orange(Fruit):
    '''
    Another way to provide substitutions.
    '''
    fruit_name = 'orange'
    # the missing fruit_attribute will be provided via template constructor

def orange_example():
    # If a substitution is provided via Template constructor,
    # it is treated as a format string and processed same way
    # as if it was defined as a class attribute.
    template = Orange(
        fruit_attribute = "{fruit_color}, period"
    )
    # provide missing fruit_color via render():
    context = template.render(fruit_color='orange')
    expected_result = "This is an orange. The orange is orange, period."
    assert context.snippet == expected_result

class Cucumber(Fruit):
    '''
    Braces escaping example.
    '''
    fruit_name = 'cucumber'
    fruit_attribute = '{{always green}}'
    # or:
    fruit_attribute = escape_braces('{always green}')

def cucumber_example():
    template = Cucumber()
    context = template.render()
    expected_result = "This is a cucumber. The cucumber is {always green}."
    assert context.snippet == expected_result

#-----------------------------------------------------------------------------------
# Dependencies

class FormattingOrderExample(Template):

    snippet = 'This snippet depends on {substitution1}.'
    substitution1 = 'the first substitution which, in turn, depends on {substitution2}'
    substitution2 = 'the second substitution which, in turn, depends on {substitution3}'
    substitution3 = 'the third substitution'

    '''
    Let's take a look at some internals:
    '''
    def render(self, *args, **kwargs):
        print(f'{self.__class__.__name__}; looking into template internals:')
        print('  data attributes:')
        for a in self._data_attributes.items():
            print(f'    {a}')
        print('  formatting order:')
        for a in self._template_attributes:
            print(f'    {a}')
        print()
        return super().render(*args, **kwargs)

def formatting_order_example():
    template = FormattingOrderExample()
    context = template.render()
    expected_result = 'This snippet depends on the first substitution which,'\
        ' in turn, depends on the second substitution which,'\
        ' in turn, depends on the third substitution.'
    assert context.snippet == expected_result


#-----------------------------------------------------------------------------------
# Data examples

class DataExamples(Template):
    '''
    Example 4.
    A bit more complex data and missing values:
    '''
    snippet1 = '''
        What is a.b[name].c[1].d? It's {a.b[name].c[1].d}!
        And what is foo.bar? {foo.bar}
        Wait, what is bar[foo][1]? {bar[foo][1]}
    '''

    a = SimpleNamespace(
        b = dict(
            name = SimpleNamespace(
                c = [
                    0,
                    SimpleNamespace(
                        d = 'wow'
                    )
                ]
            )
        )
    )

    def missing(self, name):
        return f'{name} is missing from the rendering context!'

    # Specifically, this is the case where __format__ method is required for MissingValue, see clabate/core.py:
    snippet2 = 'Missing {{baz:my format spec}}? {baz:my format spec}'

def data_example():
    template = DataExamples()
    context = template.render()
    expected_result1 = Template.dedent('''
        What is a.b[name].c[1].d? It's wow!
        And what is foo.bar? foo is missing from the rendering context!
        Wait, what is bar[foo][1]? bar is missing from the rendering context!
    ''')
    expected_result2 = 'Missing {baz:my format spec}? baz is missing from the rendering context!'
    assert context.snippet1 == expected_result1
    assert context.snippet2 == expected_result2

#-----------------------------------------------------------------------------------
# Use of properties

class PropertiesExample(Template):
    '''
    This example illustrates the ways to use properties.

    Before any value gets formatted, the rendering context is populated
    with class attributes and values passed as kwargs to the template
    constructor and the `render` method.

    Properties are evaluated lazily. Their getters are called once
    and values are cached in the rendering context.
    '''
    snippet = 'I love {something_to_love} and hate {something_to_hate}'

    @property
    # A property can use some value from the context, but
    # clabate can't detect such dependencies.
    # Here's a workaround, `depends_on` decorator.
    @depends_on('kind_of_freedom')
    def something_to_love(self, context):
        return f'{context.kind_of_freedom} freedom'

    @property
    def something_to_hate(self, context):
        value = f"{self.activist_type} activists"
        return value

    kind_of_freedom = 'absolute'

    @property
    def activist_type(self, context=None):
        # this property is invoked as usual, so the context is optional
        return 'open source'

def properties_example():
    template = PropertiesExample()
    context = template.render()
    assert context.snippet == 'I love absolute freedom and hate open source activists'

#-----------------------------------------------------------------------------------
# Arbitrary string rendering

class RenderStrExample(Template):
    '''
    Examples how to use render_str
    '''
    one = 1
    two = 2
    three = 3

    snippet = "Here's some math: {formatted_examples}"

    @property
    def formatted_examples(self, context):
        # Strings passed to render() as kwargs are not formatted,
        # but we can do that in properties usiing render_str.
        # Here, for example, we format context.examples
        # (see render(examples=...) call below:
        return self.render_str(context, context.examples)

    # Suppose you want to generate repeating pieces of same block.
    # To avoid declaring such a block inside property getter
    # you can call declare it as a class attribute and call format_str with altered substitutions

    table = '''
        +--------+--------+
        {table_rows}
        +--------+--------+
    '''

    # attributes with underscores are not formatted
    _row = '| {row_data[a]:^6} | {row_data[b]:^6} |'

    @property
    def table_rows(self, context):
        return '\n'.join(
            self.render_str(context, self._row, row_data=value)
            for value in context.table_data
        )

def render_str_example():
    template = RenderStrExample()
    context = template.render(
        examples='{one}+{two}={three}; {three}-{one}={two}',
        table_data=[dict(a=1, b=2), dict(a=3, b=4), dict(a=5, b=6)]
    )
    expected_result = "Here's some math: 1+2=3; 3-1=2"
    assert context.snippet == expected_result
    expected_table = Template.dedent('''
        +--------+--------+
        |   1    |   2    |
        |   3    |   4    |
        |   5    |   6    |
        +--------+--------+
    ''')
    assert context.table == expected_table

#-----------------------------------------------------------------------------------
# Indentation

class IndentationExample(Template):
    '''
    Demonstrate indentation.
    '''

    # All strings are dedented and the leading empty line is stripped.
    zone_config = '''
        $TTL    3600
        @   IN  SOA (
                    {primary_ns[0]}.{idna_domain}.  ; MNAME
                    {rname}  ; RNAME
                    {timestamp}  ; SERIAL
                    {cache_params}
                    )
        {nameservers}
        {resource_records}
    '''

    idna_domain = 'declassed.art'
    primary_ns = ('ns1', '1.2.3.4')
    secondary_ns = ('ns2', '5.6.7.8')

    rname = 'axy.{idna_domain}.'

    @property
    def timestamp(self, context):
        #return int(time.time())
        return 1654791702

    cache_params = '''
        3600  ; REFRESH
        60    ; RETRY
        1W    ; EXPIRY
        60    ; MINIMUM Negative Cache TTL
    '''

    @property
    def nameservers(self, context):
        # in properties dedent should be called explicitly
        tmpl = self.dedent('''
            @  IN  NS  {ns_name}.{idna_domain}.
            {ns_name}  IN  A  {ns_addr}
        ''')
        result = []
        for ns_name, ns_addr in [self.primary_ns, self.secondary_ns]:
            result.append(self.render_str(context, tmpl, ns_name=ns_name, ns_addr=ns_addr))
        return ''.join(result)

    resource_records = '''
        @  IN  A   {main_server_addr}
        *  IN  A   {main_server_addr}
    '''

    main_server_addr = '9.10.11.12'

def indentation_example():
    template = IndentationExample()
    context = template.render()
    expected_result = Template.dedent('''
        $TTL    3600
        @   IN  SOA (
                    ns1.declassed.art.  ; MNAME
                    axy.declassed.art.  ; RNAME
                    1654791702  ; SERIAL
                    3600  ; REFRESH
                    60    ; RETRY
                    1W    ; EXPIRY
                    60    ; MINIMUM Negative Cache TTL
                    )
        @  IN  NS  ns1.declassed.art.
        ns1  IN  A  1.2.3.4
        @  IN  NS  ns2.declassed.art.
        ns2  IN  A  5.6.7.8
        @  IN  A   9.10.11.12
        *  IN  A   9.10.11.12
    ''')
    assert context.zone_config == expected_result

#-----------------------------------------------------------------------------------
# LeanTemplate

class LeanTemplateExample(LeanTemplate):
    '''
    How would IndentationExample look with LeanTemplate as the base class?
    Let's simply copy-paste the code and compare.
    '''

    # All strings are dedented and the leading empty line is stripped.
    zone_config = '''
        $TTL    3600
        @   IN  SOA (
                    {primary_ns[0]}.{idna_domain}.  ; MNAME
                    {rname}  ; RNAME
                    {timestamp}  ; SERIAL
                    3600  ; REFRESH
                    60    ; RETRY
                    1W    ; EXPIRY
                    60    ; MINIMUM Negative Cache TTL
                    )
        {nameservers}
        {resource_records}
    '''

    idna_domain = 'declassed.art'
    primary_ns = ('ns1', '1,2,3,4')
    secondary_ns = ('ns2', '5,6,7,8')

    rname = 'axy.{idna_domain}.'

    @property
    def timestamp(self, context):
        #return int(time.time())
        return 1654791702

    @property
    def nameservers(self, context):
        # in properties dedent should be called explicitly
        tmpl = self.dedent('''
            @  IN  NS  {ns_name}.{idna_domain}.
            {ns_name}  IN  A  {ns_addr}
        ''')
        result = []
        for ns_name, ns_addr in [self.primary_ns, self.secondary_ns]:
            result.append(self.render_str(context, tmpl, ns_name=ns_name, ns_addr=ns_addr))
        return ''.join(result)

    resource_records = '''
        @  IN  A   {main_server_addr}
        *  IN  A   {main_server_addr}
    '''

    main_server_addr = '9.10.11.12'

def lean_template_example():
    template = LeanTemplateExample()
    context = template.render()
    expected_result = '\n'\
    '        $TTL    3600\n'\
    '        @   IN  SOA (\n'\
    '                    ns1.declassed.art.  ; MNAME\n'\
    '                    axy.declassed.art.  ; RNAME\n'\
    '                    1654791702  ; SERIAL\n'\
    '                    3600  ; REFRESH\n'\
    '                    60    ; RETRY\n'\
    '                    1W    ; EXPIRY\n'\
    '                    60    ; MINIMUM Negative Cache TTL\n'\
    '                    )\n'\
    '        \n'\
    '            @  IN  NS  ns1.declassed.art.\n'\
    '            ns1  IN  A  1,2,3,4\n'\
    '        \n'\
    '            @  IN  NS  ns2.declassed.art.\n'\
    '            ns2  IN  A  5,6,7,8\n'\
    '        \n'\
    '        \n'\
    '        @  IN  A   9.10.11.12\n'\
    '        *  IN  A   9.10.11.12\n'\
    '    \n'\
    '    '
    assert context.zone_config == expected_result

    # How about performance?
    indent_template = IndentationExample()

    start_time = time.monotonic()
    for i in range(1000):
        indent_template.render()
    indent_time = time.monotonic() - start_time

    start_time = time.monotonic()
    for i in range(1000):
        template.render()
    lean_time = time.monotonic() - start_time

    print(f'IndentedTemplate: {indent_time:.6f}s, LeanTemplate: {lean_time:.6f}')
    # on my laptop:
    # IndentedTemplate: 0.123696, LeanTemplate: 0.076246
