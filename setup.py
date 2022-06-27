import os
import setuptools

import clabate

with open(os.path.join(os.path.dirname(__file__), 'README')) as f:
    _long_description = f.read()

setuptools.setup(
    name         = 'clabate',
    version      = clabate.__version__,
    author       = 'AXY',
    author_email = 'axy@declassed.art',
    description  = 'Minimalistic class-based templates',

    long_description = _long_description,
    long_description_content_type = 'text/plain',

    url = 'https://declassed.art/repository/clabate',

    packages = [
        'clabate',
        'clabate.extras',
        'clabate.examples'
    ],

    classifiers = [
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Development Status :: 4 - Beta',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Text Processing :: Markup :: HTML'
    ],

    python_requires = '>=3.6',
)
