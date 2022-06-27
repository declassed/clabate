'''
File inclusion examples.

:copyright: Copyright 2021-2022 AXY axy@declassed.art
:license: BSD, see LICENSE for details.
'''

import os

from .. import MarkupTemplate, Markup
from ..extras.inclusion import FileReaderMixin, BadPathError

class BaseTemplate(
        MarkupTemplate,
        FileReaderMixin(
            'examples',  # attribute name to invoke file inclusion
            os.path.dirname(__file__)  # base directory name
        )
      ):
    pass

class TemplateWithEscapedInclusion(BaseTemplate):
    '''
    The content returned by :read method gets escaped inside markup.
    '''
    snippet = Markup('''
        <h1>Content of file_inclusion.html</h1>
        <pre>
        {examples:read('file_inclusion.html')}
        </pre>
    ''')

def escaped_inclusion_example():
    template = TemplateWithEscapedInclusion()
    context = template.render()
    # Included file should be properly escaped:
    expected_result = MarkupTemplate.dedent('''
        <h1>Content of file_inclusion.html</h1>
        <pre>
        &lt;div&gt;
            Sample &lt;strong&gt;inclusion&lt;/strong&gt; file.
        &lt;/div&gt;
        </pre>
    ''')
    assert context.snippet == expected_result

class TemplateWithMarkupInclusion(BaseTemplate):
    '''
    Use :read_markup to include markup as is.
    '''
    snippet = Markup('''
        <h1>Content of file_inclusion.html</h1>
        <pre>
        {examples:read_markup('file_inclusion.html')}
        </pre>
    ''')

    # Same as above but file name is passed via substitution.
    filename = 'file_inclusion.html'

    # Mind !r conversion to make invocation syntactically correct!
    snippet2 = Markup('''
        <h1>Content of file_inclusion.html</h1>
        <pre>
        {examples:read_markup({filename!r})}
        </pre>
    ''')

def markup_inclusion_example():
    template = TemplateWithMarkupInclusion()
    context = template.render()
    expected_result = MarkupTemplate.dedent('''
        <h1>Content of file_inclusion.html</h1>
        <pre>
        <div>
            Sample <strong>inclusion</strong> file.
        </div>
        </pre>
    ''')
    assert context.snippet == expected_result

class BadPathTemplate1(BaseTemplate):
    '''
    file paths outside the root directory should fail
    '''
    snippet = Markup("{examples:read('../core.py')}")

def bad_path1_example():
    template = BadPathTemplate1()
    try:
        context = template.render()
        assert False, 'WTF??? this should fail!'
    except BadPathError:
        print('Access blocked, that\'s good')

class BadPathTemplate2(BaseTemplate):
    '''
    File paths outside the root directory should fail
    '''
    snippet = Markup("{examples:read('foo/bar/../../../core.py')}")

def bad_path2_example():
    template = BadPathTemplate2()
    try:
        context = template.render()
        assert False, 'WTF??? this should fail!'
    except BadPathError:
        print('Access blocked, that\'s good')

class BadPathTemplate3(BaseTemplate):
    '''
    Simply bad path should cause bare Exception
    '''
    snippet = Markup("{examples:read('/core.py')}")

def bad_path3_example():
    template = BadPathTemplate3()
    try:
        context = template.render()
        assert False, 'WTF??? this should fail!'
    except Exception as e:
        assert e.__class__.__name__ == 'Exception'
        print(f'Bad path caused an exception {e.__class__.__name__}, that\'s good')
