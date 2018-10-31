"""
Tests for the blockstore API utils.
"""

import ddt
from django.test import TestCase

from ..utils import ZippableMultiValueDict


@ddt.ddt
class ZippableMultiValueDictTestCase(TestCase):
    @ddt.data(
        ({
            'data': ['text file', '<html>file</html>'],
            'path': ['c/file-4.txt', 'c/file-5.html'],
            'public': [True, False]
         },
         [
            {'data': 'text file', 'path': 'c/file-4.txt', 'public': True},
            {'data': '<html>file</html>', 'path': 'c/file-5.html', 'public': False},
         ]),
        ({
            'data': ['text file', '<html>file</html>'],
            'path': [None, 'c/file-5.html'],
            'public': [False]
         },
         [
            {'data': 'text file', 'path': None, 'public': False},
            {'data': '<html>file</html>', 'path': 'c/file-5.html'},
         ]),
    )
    @ddt.unpack
    def test_flatten(self, mvd, expected):
        zippable = ZippableMultiValueDict(mvd)
        zipped = zippable.zip()
        assert zipped == expected
