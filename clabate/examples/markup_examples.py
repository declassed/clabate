'''
Markup examples.

:copyright: Copyright 2021-2022 AXY axy@declassed.art
:license: BSD, see LICENSE for details.
'''

from types import SimpleNamespace

from ..markup import MarkupTemplate, Markup

class HtmlBoilerplate(MarkupTemplate):

    html = Markup('''
        <html>
        {head}
        {body}
        </html>
    ''')

    head = Markup('''
        <head>
            <title>{title}</title>
        </head>
    ''')

    title = 'Example'

    body = Markup('''
        <body>
            <header>
                {header}
            </header>
            <main>
                {main}
            </main>
            <footer>
                {footer}
            </footer>
        </body>
    ''')

    header = Markup('This is <strong>header</strong>.')

    main = Markup('Main content goes <strong>here</strong>.')

    footer = Markup('This is <strong>footer</strong>.')

def html_boilerplate_example():
    template = HtmlBoilerplate()
    context = template.render()
    expected_result = MarkupTemplate.dedent('''
        <html>
        <head>
            <title>Example</title>
        </head>
        <body>
            <header>
                This is <strong>header</strong>.
            </header>
            <main>
                Main content goes <strong>here</strong>.
            </main>
            <footer>
                This is <strong>footer</strong>.
            </footer>
        </body>
        </html>
    ''')
    assert context.html == expected_result


class EscapingExample(MarkupTemplate):
    '''
    All values are escaped. Including complex data and missing values:
    '''
    attr1 = 'String attributes are <strong>escaped</strong>'
    snippet1 = '''
        {attr1}
        {init_kwarg}
        {render_kwarg}
        What is <a.b[name].c[1].d>? It's {a.b[name].c[1].d}!
        And what is foo.bar? {foo.bar}
    '''

    a = SimpleNamespace(
        b = dict(
            name = SimpleNamespace(
                c = [
                    0,
                    SimpleNamespace(
                        d = '<wow>'
                    )
                ]
            )
        )
    )
    result1 = MarkupTemplate.dedent('''
        String attributes are &lt;strong&gt;escaped&lt;/strong&gt;
        __init__ kwargs are &lt;strong&gt;escaped&lt;/strong&gt;
        render kwargs are &lt;strong&gt;escaped&lt;/strong&gt;
        What is &lt;a.b[name].c[1].d&gt;? It's &lt;wow&gt;!
        And what is foo.bar? &lt;foo&gt; is missing from the rendering context!
    ''')

    '''
    And values are escaped only once!
    '''
    snippet2 = '''
        Values are escaped only once:{snippet1}
        Otherwise we'd get &amp;
    '''
    result2 = MarkupTemplate.dedent('''
        Values are escaped only once:
        String attributes are &lt;strong&gt;escaped&lt;/strong&gt;
        __init__ kwargs are &lt;strong&gt;escaped&lt;/strong&gt;
        render kwargs are &lt;strong&gt;escaped&lt;/strong&gt;
        What is &lt;a.b[name].c[1].d&gt;? It's &lt;wow&gt;!
        And what is foo.bar? &lt;foo&gt; is missing from the rendering context!

        Otherwise we'd get &amp;amp;
    ''')

    def missing(self, name):
        return f'<{name}> is missing from the rendering context!'

class GoodTemplate3(MarkupTemplate):

    '''
    Example 3.
    Same as example 2, but use markup:
    '''
    attr1 = Markup('Markup attributes are <strong>unchanged</strong>')
    snippet1 = Markup('''
        {attr1}
        {init_kwarg}
        {render_kwarg}
        What is <a.b[name].c[1].d>? It's {a.b[name].c[1].d}!
        What is <a.b[name].c[1].e>? It's {a.b[name].c[1].e} and it is escaped!
        And what is foo.bar? {foo.bar}
    ''')

    a = SimpleNamespace(
        b = dict(
            name = SimpleNamespace(
                c = [
                    0,
                    SimpleNamespace(
                        d = Markup('<span style="color:green">wow</span>'),
                        e = '<span style="color:green">wow</span>'
                    )
                ]
            )
        )
    )
    result1 = MarkupTemplate.dedent('''
        Markup attributes are <strong>unchanged</strong>
        __init__ kwargs are <strong>unchanged</strong>
        render kwargs are <strong>unchanged</strong>
        What is <a.b[name].c[1].d>? It's <span style="color:green">wow</span>!
        What is <a.b[name].c[1].e>? It's &lt;span style="color:green"&gt;wow&lt;/span&gt; and it is escaped!
        And what is foo.bar? <span style="color:red">foo</span> is missing from the rendering context!
    ''')

    def missing(self, name):
        return Markup(f'<span style="color:red">{name}</span> is missing from the rendering context!')

    '''
    And values are escaped only once!
    '''
    snippet2 = Markup('''
        Values are escaped only once:{snippet1}
        Otherwise we'd get &amp; instead of bare &
    ''')
    result2 = MarkupTemplate.dedent('''
        Values are escaped only once:
        Markup attributes are <strong>unchanged</strong>
        __init__ kwargs are <strong>unchanged</strong>
        render kwargs are <strong>unchanged</strong>
        What is <a.b[name].c[1].d>? It's <span style="color:green">wow</span>!
        What is <a.b[name].c[1].e>? It's &lt;span style="color:green"&gt;wow&lt;/span&gt; and it is escaped!
        And what is foo.bar? <span style="color:red">foo</span> is missing from the rendering context!

        Otherwise we'd get &amp; instead of bare &
    ''')

    '''
    XXX
    if a property getter returns Markup, it's user responsibility to escape substitutions
    '''
    @property
    def long_description(self, context):
        return ' '.join((context.short_description, context.description))

class GoodTemplate4(MarkupTemplate):

    '''
    Example 4.
    Tag attributes.
    '''
    snippet1 = Markup('''
        <span data-link="{link1}">wrong attribute escaping</span>
    ''')
    link1 = '<a href="https://declassed.art">declassed.art</a>'
    result1 = MarkupTemplate.dedent('''
        <span data-link="&lt;a href="https://declassed.art"&gt;declassed.art&lt;/a&gt;">wrong attribute escaping</span>
    ''')

    snippet2 = Markup('''
        <span data-link={link2}>correct attribute escaping</span>
    ''')

    snippet3 = Markup('''
        <span data-link={escape:attr('<a href="https://declassed.art">declassed.art</a>')}>inline attribute escaping</span>
    ''')
    result3 = MarkupTemplate.dedent('''
        <span data-link='&lt;a href="https://declassed.art"&gt;declassed.art&lt;/a&gt;'>inline attribute escaping</span>
    ''')

    snippet4 = Markup('''
        Inline javascript attribute escaping
        <p onclick={escape:attr("""
            run("<script>this()</script>");
            run('<script>that()</script>');
        """)}>Click me!</p>
    ''')
    result4 = MarkupTemplate.dedent('''
        Inline javascript attribute escaping
        <p onclick="run(&quot;&lt;script&gt;this()&lt;/script&gt;&quot;);&#10;    run('&lt;script&gt;that()&lt;/script&gt;');">Click me!</p>
    ''')

class MarkupInsideNonMarkup(MarkupTemplate):
    '''
    What if we insert markup in a non-markup?
    Suppose we want to insert some markup in a text to be escaped.
    '''
    # Some markup. Escape marks it as Escaped.
    # No actual escaping is performed because it's already markup.
    some_markup = Markup("""<span style="color:red">your custom HTML</span>""")

    # First snippet. Literal text around substitution is escaped by formatter.
    # Substitution is already escaped so copied to the resulting string as is.
    # The result is marked as Escaped.
    snippet1 = '''
        When a text is going to be <escaped> but you need
        to insert {some_markup}
    '''

    # Another way to do the above. The result is exactly the same.
    snippet2 = '''
        When a text is going to be <escaped> but you need
        to insert {escape:markup("""<span style="color:red">your custom HTML</span>""")}
    '''

    # Third snippet. Literal text around substitutions is escaped by formatter.
    # Substitutions are already escaped so copied to the resulting string as is.
    # No double escaping takes place for substitutions.
    snippet3 = '''
        Doubly escaped?
        {snippet1}
        {snippet2}
        -- No!
    '''

    # Fourth snippet. Same as in third one, the substitution is already escaped
    # and no triple escaping takes place.
    snippet4 = '''
        Triply escaped?
        {snippet3}
        -- No!
    '''

def markup_inside_non_markup_example():
    template = MarkupInsideNonMarkup()
    context = template.render()
    expected_result = MarkupTemplate.dedent('''
        When a text is going to be &lt;escaped&gt; but you need
        to insert <span style="color:red">your custom HTML</span>
    ''')
    print()
    print('=== here is snippet4 from MarkupInsideNonMarkup which demonstrates that values are escaped only once ===')
    print(context.snippet4)
    print()
    assert context.snippet1 == expected_result
    assert context.snippet2 == expected_result
    assert '&lt;span' not in context.snippet3
    assert '&amp' not in context.snippet4

class TagAttrInsideNonMarkup(MarkupTemplate):
    '''
    How about escaping tag attribute in a non-markup?
    '''
    snippet = """<span data-link={escape:attr('<a href="https://declassed.art">declassed.art</a>')}>inline attribute escaping</span>"""

    snippet2 = Markup('''
            <p onclick={escape:attr("""
                do_this('asd');
                do_that("sdf");
            """)}>Click me!</p>
    ''')

def tag_attr_inside_non_markup_example():
    template = TagAttrInsideNonMarkup()
    context = template.render()
    expected_result = """&lt;span data-link='&amp;lt;a href="https://declassed.art"&amp;gt;declassed.art&amp;lt;/a&amp;gt;'&gt;inline attribute escaping&lt;/span&gt;"""
    assert context.snippet == expected_result

class FormatSpecEscapeTemplate(MarkupTemplate):
    '''
    Format specification is escaped because of recursive nature of `string.Formatter.vformat()` method.
    '''
    snippet = '''
        This is a <literal text> preceeding the {substitution: And this is a <literal text>
        for {nested_substitution: which gets <doubly escaped> if not a markup!}}
    '''

    class MarkupSubst:
        def __format__(self, format_spec):
            return Markup(format_spec)

    class PlainSubst:
        def __format__(self, format_spec):
            return format_spec

    substitution = MarkupSubst()
    nested_substitution = PlainSubst()

def format_spec_escape_example():
    template = FormatSpecEscapeTemplate()
    context = template.render()
    expected_result = MarkupTemplate.dedent('''
        This is a &lt;literal text&gt; preceeding the  And this is a &lt;literal text&gt;
        for  which gets &amp;lt;doubly escaped&amp;gt; if not a markup!
    ''')
    assert context.snippet == expected_result


#-----------------------------------------------------------------------------------
# Arbitrary string rendering
# copy-pasted from basic examples, make notes on escapiing inside properties!!!
# do HTML table example, please

class RenderStrExample(MarkupTemplate):
    '''
    Examples how to use render_str
    '''
    one = 1
    two = 2
    three = 3

    snippet = "Here's some math: {formatted_examples}"

    @property
    def formatted_examples(self, context):
        # strings passed to render() are not formatted but we can do that here:
        return self.render_str(context, context.examples)

    # Suppose you want to generate repeating pieces of same block.
    # To avoid declaring such a block inside property getter
    # you can call declare it as a class attribute and call format_str with altered substitutions

    table = '''
        +--------+--------+
        {table_rows}
        +--------+--------+
    '''

    xxx = '|'

    # attributes with underscores are not formatted
    _row = '{xxx} {row_data[a]:^6} | {row_data[b]:^6} {xxx}'

    @property
    def table_rows(self, context):
        return '\n'.join(
            self.render_str(context, self._row, row_data=value)
            for value in context.table_data
        )

def render_str_example():

    template = RenderStrExample()
    context = template.render(
        examples = '{one}+{two}={three}; {three}-{one}={two}',
        table_data = [dict(a=1, b=2), dict(a=3, b=4), dict(a=5, b=6)]
    )
    expected_result = "Here's some math: 1+2=3; 3-1=2"
    assert context.snippet == expected_result
    expected_table = MarkupTemplate.dedent('''
        +--------+--------+
        |   1    |   2    |
        |   3    |   4    |
        |   5    |   6    |
        +--------+--------+
    ''')
    assert context.table == expected_table
