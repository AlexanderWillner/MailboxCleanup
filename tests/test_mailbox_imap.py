#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Module documentation goes here."""


import email
import imaplib
import unittest
from src.mailbox_imap import MailboxCleanerIMAP
from tests.test_mailbox_abstract import TestMailboxAbstract


class TestMailboxCleanerIMAP(TestMailboxAbstract, unittest.TestCase):
    """Class documentation goes here."""
    class _ImapMockup():
        def __init__(self):
            test_input = 'tests/test.eml'
            with open(test_input) as filepointer:
                self.msg = email.message_from_file(filepointer)

        @staticmethod
        def login(user=None, _password=None):
            """Mocking login."""
            if user != 'test':
                raise imaplib.IMAP4.error('wrong username')

        @staticmethod
        def logout():
            """Mocking logout."""
            return ('OK', None)

        @staticmethod
        def close():
            """Mocking close."""
            return ('OK', None)

        @staticmethod
        def expunge():
            """Mocking expunge."""
            return ('OK', None)

        @staticmethod
        def select(_folder, readonly=True):
            """Mocking select."""
            return ('OK', readonly)

        @staticmethod
        def append(_folder, _flags, _date, _msg):
            """Mocking append."""
            return ('OK', None)

        @staticmethod
        def list():
            """Mocking list."""
            folders = [b'(\\Marked \\HasNoChildren) "/" Inbox',
                       b'(\\Marked \\HasChildren) "/" Archive',
                       b'(\\HasNoChildren) "/" "Archive/Test"']
            return ('OK',
                    folders)

        def uid(self, command, _a=None, _b=None, _c=None):
            """Mocking uid."""
            result = 'OK'
            if command == 'search':
                data = [b'142627 142632 142633 142640 142641']
            elif command == 'fetch':
                data = [(b'10 (UID 142684 BODY[] {2617453}',
                        self.msg.as_bytes()),
                        b' FLAGS (\\Seen \\Recent))']
            else:
                data = None
            return (result, data)

    def test_basics(self):
        """Testing basic class."""

        imap = MailboxCleanerIMAP(self.args)
        with self.assertRaises((ConnectionRefusedError,
                                SystemExit)):
            imap.login()

        imap._load_cache()  # pylint: disable=W0212
        imap.cleanup()

    def test_with_mockup(self):
        """Testing with mockup class."""

        mockup = self._ImapMockup()
        imap = MailboxCleanerIMAP(self.args, mockup)
        imap.process_folders()
        imap.login()
        imap.logout()

        self.args.user = 'invalid'
        with self.assertRaises(SystemExit):
            imap = MailboxCleanerIMAP(self.args, mockup)
            imap.login()

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
