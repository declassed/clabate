'''
Run examples.

:copyright: Copyright 2022 AXY axy@declassed.art
:license: BSD, see LICENSE for details.
'''

import importlib
from glob import iglob
import os.path
import sys
import traceback

def run_examples():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))  # XXX get rid of dirname
    for filename in iglob(os.path.join(os.path.dirname(__file__), '*.py')):
        if os.path.abspath(filename) == os.path.abspath(__file__):
            continue
        module_name = os.path.splitext(os.path.basename(filename))[0]
        if module_name == '__init__':
            continue
        module = importlib.import_module('.' + module_name, 'clabate.examples')

        # collect examples
        examples = []
        for name in dir(module):
            if name.endswith('_example'):
                example = getattr(module, name)
                if callable(example):
                    examples.append(example)

        if not examples:
            print(f'No examples in {module_name}')
            continue

        print(f'Running examples from {module_name}')
        for example in examples:
            try:
                example()
                print(f'{example.__name__}: OK')
            except Exception:
                print(f'{example.__name__}: ERROR:\n{traceback.format_exc()}')
        print()

if __name__ == '__main__':
    try:
        run_examples()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
