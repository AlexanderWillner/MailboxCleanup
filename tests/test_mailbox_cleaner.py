#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Module documentation goes here."""


import unittest
from src import mailbox_cleaner
from tests.test_mailbox_abstract import TestMailboxAbstract


class TestMailboxCleaner(TestMailboxAbstract, unittest.TestCase):
    """Class documentation goes here."""

    def test_cli(self):
        """Testing the CLI."""

        with self.assertRaises(SystemExit) as code:
            mailbox_cleaner.main()

        self.assertEqual(code.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
