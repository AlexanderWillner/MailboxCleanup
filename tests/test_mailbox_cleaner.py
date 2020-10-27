#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Module documentation goes here."""


import unittest
import sys
from unittest.mock import patch
from src import mailbox_cleaner
from tests.test_mailbox_abstract import TestMailboxAbstract


class TestMailboxCleaner(TestMailboxAbstract, unittest.TestCase):
    """Class documentation goes here."""

    def test_cli(self):
        """Testing the CLI."""

        with self.assertRaises(SystemExit) as code:
            mailbox_cleaner.main()

        self.assertEqual(code.exception.code, 2)

        testargs = ["prog", "-s unknown.localhost", "-u test", "-p test"]
        with patch.object(sys, 'argv', testargs):
            with self.assertRaises(SystemExit) as code:
                mailbox_cleaner.main()

            self.assertTrue("Errno 8" in code.exception.code)


if __name__ == '__main__':
    unittest.main()
