'''
Helpers to generate sequential values.

:copyright: Copyright 2019-2021 AXY axy@declassed.art
:license: BSD, see LICENSE for details.
'''

import threading

from ..invoke import Invoke

class Sequence(threading.local, Invoke):
    '''
    `Sequence` class provides methods to generate sequential values.
    For retaining thread safety this class is based on `threading.local`.
    '''
    def first(self, value=1):
        '''
        Initialize sequence with a `value`.
        '''
        self.i = value
        return str(value)

    def next(self, value=None):
        '''
        Generate next value or re-initialize sequence with new `value`.
        '''
        if value is None:
            self.i += 1
        else:
            self.i = value
        return str(self.i)

    def prev(self, value=None):
        '''
        Generate previous value or re-initialize sequence with new `value`.
        '''
        if value is None:
            self.i -= 1
        else:
            self.i = value
        return str(self.i)

def SequenceMixin(sequence_attribute_name):
    '''
    Create sequence mixin for templates.

    Usage::

        class MyTemplate(Template, SequenceMixin('seq')):
            ...

    In the template:

    1. Initialize the sequence, i.e. start from 5::

        {seq:first(5)}

    2. Generate numbers 6, 7, 8, 10, 9::

        {seq:next()},
        {seq:next()},
        {seq:next()}
        {seq:next(10)}
        {seq:prev()}

    '''
    return type('SequenceMixin', (object,), {sequence_attribute_name: Sequence()})
