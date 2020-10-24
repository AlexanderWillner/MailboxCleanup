#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Module documentation goes here."""

import email
import logging
import unittest
from src.mailbox_cleaner import MailboxCleaner


class MyTestCase(unittest.TestCase):
    """Class documentation goes here."""

    class _Namespace:  # pylint: disable=R0903
        """Helper class for arguments."""

        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.args = self._Namespace(server='example.org',
                                    max_size=20,
                                    skip_download=False,
                                    detach=False,
                                    target='/tmp/mailbox_cleaner')

    def test_get_tags(self):
        """Testing flag extraction."""

        test_input = [(b'1 (RFC822 {242020}', b'\r\n'),
                      b' UID 142377 FLAGS (\\Seen \\Recent NotJunk)']
        test_output = MailboxCleaner.get_flags_from_struct(test_input)
        print("Result: ", test_output)
        self.assertTrue("Seen" in test_output)
        self.assertTrue("NotJunk" in test_output)
        self.assertFalse("Recent" in test_output)

    # def test_convert_date(self):
    #     """Testing date conversion."""

    #     test_input = "Thu, 22 Oct 2020 12:38:26 +0200"
    #     test_output = MailboxCleaner.convert_date(test_input)
    #     test_expectation = '"22-Oct-2020 12:38:26 +0200"'
    #     print("Result: ", test_output)
    #     self.assertEqual(test_output, test_expectation)

    def test_convert_filename(self):
        """Testing decoding filenames."""

        test_input = "=?iso-8859-1?Q?2=5FB=FCrg=5F_Br?= =?iso-8859-1?Q?l.p?="
        test_output = MailboxCleaner.convert_filename(test_input)
        test_expectation = '2_Bürg_ Brl.p'
        print("Result: ", test_output)
        self.assertEqual(test_output, test_expectation)

        test_input = "file/with/slash.pdf"
        test_output = MailboxCleaner.convert_filename(test_input)
        test_expectation = 'file_with_slash.pdf'
        print("Result: ", test_output)
        self.assertEqual(test_output, test_expectation)

    def test_detach_attachment(self):
        """Testing detaching attachments."""

        test_input = 'tests/test.eml'
        test_expectation = 'removed-fed00c051c9f991a8a2d19dcadcf5ff3.jpg.txt'

        with open(test_input) as filepointer:
            msg = email.message_from_file(filepointer)

        self.assertFalse(test_expectation in msg.as_string())
        cleaner = MailboxCleaner(self.args)
        modified = cleaner.download_and_detach_attachments(msg)
        self.assertTrue(modified)
        self.assertTrue(test_expectation in msg.as_string())
        modified = cleaner.download_and_detach_attachments(msg)
        self.assertFalse(modified)


if __name__ == '__main__':
    unittest.main()
