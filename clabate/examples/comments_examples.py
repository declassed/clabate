'''
Comments examples.

:copyright: Copyright 2021-2022 AXY axy@declassed.art
:license: BSD, see LICENSE for details.
'''

from .. import Template

class TemplateWithComments(Template):

    # Comments may span multiple lines.
    snippet1 = '''
        The red dog
        {comment: or fox?}
        jumps over the lazy fox.{comment: at last, maybe it's
        a fox who jumps over the lazy dog?}
    '''

    # Braces in comments should be escaped, otherwise they are treated as substitutions.
    snippet2 = "{comment: Braces should be escaped like this: {{ }}, otherwise it's a {substitution}}"
    substitution = 'blah blah blah'

def comments_example():
    template = TemplateWithComments()
    context = template.render()
    expected_result1 = Template.dedent('''
        The red dog

        jumps over the lazy fox.
    ''')
    assert context.snippet1 == expected_result1
    assert context.snippet2 == ''
