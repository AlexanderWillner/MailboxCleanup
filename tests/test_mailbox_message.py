#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Module documentation goes here."""

import email
import unittest
from src.mailbox_message import MailboxCleanerMessage
from tests.test_mailbox_abstract import TestMailboxAbstract


class TestMailboxMessage(TestMailboxAbstract, unittest.TestCase):
    """Class documentation goes here."""

    def test_convert_filename(self):
        """Testing decoding filenames."""

        test_input = "=?iso-8859-1?Q?2=5FB=FCrg=5F_Br?= =?iso-8859-1?Q?l.p?="
        test_output = MailboxCleanerMessage.convert_filename(test_input)
        test_expectation = '2_Bürg_ Brl.p'
        print("Result: ", test_output)
        self.assertEqual(test_output, test_expectation)

        test_input = "file/with/slash.pdf"
        test_output = MailboxCleanerMessage.convert_filename(test_input)
        test_expectation = 'file_with_slash.pdf'
        print("Result: ", test_output)
        self.assertEqual(test_output, test_expectation)

    def test_download_attachment(self):
        """Testing downloading attachments."""

        test_input = 'tests/test.eml'

        with open(test_input) as filepointer:
            msg = email.message_from_file(filepointer)

        message = MailboxCleanerMessage(self.args)
        uid = MailboxCleanerMessage.get_uid(msg)
        expected = 'E280C461-3229-4671-82B5-8F10E6866E9D@server.example.org'
        self.assertEqual(uid, expected)

        message.download_attachment(msg)

        self.args.skip_download = True
        message.download_attachment(msg)

    def test_detach_attachment(self):
        """Testing detaching attachments."""

        test_input = 'tests/test.eml'
        test_expectation = 'removed-fed00c051c9f991a8a2d19dcadcf5ff3.jpg.txt'

        with open(test_input) as filepointer:
            msg = email.message_from_file(filepointer)

        self.assertFalse(test_expectation in msg.as_string())
        message = MailboxCleanerMessage(self.args)
        modified = message.download_and_detach_attachments(msg)
        self.assertTrue(modified)
        self.assertTrue(test_expectation in msg.as_string())
        modified = message.download_and_detach_attachments(msg)
        self.assertFalse(modified)

    def test_process_folder_locally(self):
        """Testing local eml file processing."""

        cleaner = MailboxCleanerMessage(self.args)
        cleaner.process_directory(self._void)

    def _void(self, param):
        """Helper function for testing."""


if __name__ == '__main__':
    unittest.main()
