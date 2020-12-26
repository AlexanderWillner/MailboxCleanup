#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Module documentation goes here."""


import unittest
import sys
from unittest.mock import patch
from src import mailbox_cli
from tests.test_mailbox_abstract import TestMailboxAbstract


class TestMailboxCleanerCLI(TestMailboxAbstract, unittest.TestCase):
    """Class documentation goes here."""

    def test_cli(self):
        """Testing the CLI."""

        with self.assertRaises(SystemExit) as code:
            mailbox_cli.main()

        self.assertEqual(code.exception.code, 2)

        testargs = ["prog", "-s unknown.localhost", "-u test", "-p test"]
        with patch.object(sys, 'argv', testargs):
            with self.assertRaises(SystemExit) as code:
                mailbox_cli.main()
            self.assertTrue("wrong server?" in code.exception.code)


if __name__ == '__main__':
    unittest.main()
