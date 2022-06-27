'''
File inclusion helpers.

:copyright: Copyright 2019-2021 AXY axy@declassed.art
:license: BSD, see LICENSE for details.
'''

import os

from ..invoke import Invoke
from ..markup import Markup

class BadPathError(Exception):
    pass

class FileReader(Invoke):
    '''
    `FileReader` class provides inclusion methods to use in templates.
    '''
    def __init__(self, root_directory):
        # make sure root_directory is absolute
        if not os.path.isabs(root_directory):
            root_directory = os.path.abspath(root_directory)
        # resolve symbolic links if any
        self.root_directory = os.path.realpath(root_directory)

    def read(self, filename, encoding='utf-8'):
        '''
        Read text file.
        '''
        # normalize filename
        normalized_filename = os.path.normpath(filename)
        if os.path.isabs(normalized_filename):
            raise Exception(f'File name should be relative: {filename}')
        normalized_filename = os.path.realpath(os.path.join(self.root_directory, normalized_filename))
        # check filename is within root directory
        if os.path.commonpath([self.root_directory, normalized_filename]) != self.root_directory:
            raise BadPathError(f'Real file name of {filename} is outside root directory: {self.root_directory}')
        # read file
        with open(normalized_filename, 'r', encoding=encoding) as f:
            return f.read()

    def read_markup(self, filename, encoding='utf-8'):
        '''
        Read text file and return Markup object.
        '''
        return Markup(self.read(filename, encoding=encoding))

def FileReaderMixin(name, root_directory):
    '''
    Highlighting mixin for templates.

    Usage::

        class Template(FileReaderMixin('articles', os.path.join(app_dir, 'articles'))):
            ...

    In the template:

        {articles:read('my-article')}
        {articles:read_markup('my-article')}
    '''
    return type('FileReaderMixin', (object,), {name: FileReader(root_directory)})
