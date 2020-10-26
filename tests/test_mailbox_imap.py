#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Module documentation goes here."""


import unittest
from src.mailbox_imap import MailboxCleanerIMAP
from tests.test_mailbox_abstract import TestMailboxAbstract


class TestMailboxCleanerIMAP(TestMailboxAbstract, unittest.TestCase):
    """Class documentation goes here."""

    def test_basics(self):
        """Testing basic class."""

        imap = MailboxCleanerIMAP(self.args)
        with self.assertRaises(SystemExit) as error:
            imap.login()
        self.assertTrue("wrong server" in error.exception.code)

        imap._load_cache()  # pylint: disable=W0212
        imap.cleanup()

    def test_get_tags(self):
        """Testing flag extraction."""

        test_input = [(b'1 (RFC822 {242020}', b'\r\n'),
                      b' UID 142377 FLAGS (\\Seen \\Recent NotJunk)']
        test_output = MailboxCleanerIMAP.get_flags_from_struct(test_input)
        print("Result: ", test_output)
        self.assertTrue("Seen" in test_output)
        self.assertTrue("NotJunk" in test_output)
        self.assertFalse("Recent" in test_output)

    def test_convert_date(self):
        """Testing date conversion."""

        test_input = "Thu, 22 Oct 2020 12:38:26 +0200"
        test_output = MailboxCleanerIMAP.convert_date(test_input)
        test_expectation = '22-Oct-2020'
        print("Result: ", test_output)
        self.assertTrue(test_expectation in test_output)

    def test_struct(self):
        """Testing struct parser."""

        test_input = [(b'1 (RFC822 {242020}', b'\x80abc'),
                      b' UID 142377 FLAGS (\\Seen \\Recent NotJunk)']
        test_output = MailboxCleanerIMAP.get_msg_from_struct(test_input)
        test_output = test_output.as_string()
        test_expectation = 'abc'
        print("Result: '%s'" % test_output)
        self.assertTrue(test_expectation in test_output)


if __name__ == '__main__':
    unittest.main()