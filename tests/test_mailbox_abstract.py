#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Module documentation goes here."""


import logging
import unittest
import tempfile


class TestMailboxAbstract(unittest.TestCase):
    """Class documentation goes here."""
    # pylint: disable=R0801
    class _Namespace:  # pylint: disable=R0903, R0801
        """Helper class for arguments."""

        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    _TARGET = tempfile.mkdtemp() + '_'

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.args = self._Namespace(server='unknown.localhost',
                                    max_size=20,
                                    skip_download=False,
                                    detach=True,
                                    target=TestMailboxAbstract._TARGET,
                                    upload='tests',
                                    folder='tests',
                                    reset_cache=True)
