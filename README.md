# Minimalistic class-based templates for Python

This is a backup of the official repository https://declassed.art/repository/clabate

Clabate is a minimalistic template system for Python language.
It utilizes python class hierarchy, class attributes, and
[PEP 3101](https://www.python.org/dev/peps/pep-3101) string formatting.

The basic Template class can be used for bare textual templates, such as configuration files.

For markup, Clabate escapes everything by default, helping to avoid overlooked unescaped substitutions
as much as possible.

You can find more or less comprehensive examples under clabate/examples which is also a simple test suite.

An introduction to Clabate:
https://declassed.art/en/blog/2022/06/29/clabate-class-based-templates

```python
from clabate import MarkupTemplate, Markup

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

class HomePageTemplate(HtmlBoilerplate):

    title = '{greeting}!'
    header = Markup('<h1>Home page</h1>')
    main = '{greeting} home'
    footer = ''

    @property
    def greeting(self, context=None):
        # some dynamic content
        if self.is_good_phase_of_moon():
            return 'Welcome'
        else:
            return 'F#ck'

    def is_good_phase_of_moon(self):
        from time import time
        return int(time()) % 5

template = HomePageTemplate()
context = template.render()
print(context.html)
```
