'''
Pygments examples.

:copyright: Copyright 2021-2022 AXY axy@declassed.art
:license: BSD, see LICENSE for details.
'''

from ..markup import MarkupTemplate
from ..extras.pygments import PygmentsMixin

class BasicExample(MarkupTemplate, PygmentsMixin):

    snippet = '''
        {pygments:highlight('python', """
            def main():
                # XXX: simple thing
                print('Hello, world!')
        """)}
    '''

def pygments_example():
    template = BasicExample()
    context = template.render()
    expected_result = MarkupTemplate.dedent('''
        <div class="highlight"><pre><span></span><span class="k">def</span> <span class="nf">main</span><span class="p">():</span>
            <span class="c1"># XXX: simple thing</span>
            <span class="nb">print</span><span class="p">(</span><span class="s1">&#39;Hello, world!&#39;</span><span class="p">)</span>
        </pre></div>
    ''')
    assert context.snippet.strip() == expected_result.strip()

class FiltersExample(MarkupTemplate, PygmentsMixin):

    snippet = '''
        {pygments:highlight('python', """
            def main():
                # XXX: simple thing
                print('Hello, world!')
        """,
        filters = [('codetagify', {{}})])}
    '''

def pygments_filters_example():
    template = FiltersExample()
    context = template.render()
    expected_result = MarkupTemplate.dedent('''
        <div class="highlight"><pre><span></span><span class="k">def</span> <span class="nf">main</span><span class="p">():</span>
            <span class="c1"># </span><span class="cs">XXX</span><span class="c1">: simple thing</span>
            <span class="nb">print</span><span class="p">(</span><span class="s1">&#39;Hello, world!&#39;</span><span class="p">)</span>
        </pre></div>
    ''')
    assert context.snippet.strip() == expected_result.strip()
