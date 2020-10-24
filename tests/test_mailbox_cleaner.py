#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Module documentation goes here."""

import unittest
import sys
from src.mailbox_cleaner import MailboxCleaner
from email.message import EmailMessage
import email
import logging

class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class MyTestCase(unittest.TestCase):
    """Class documentation goes here."""

    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        self.args = Namespace(server='example.org',
                              max_size=20,
                              skip_download = False,
                              target = '/tmp/mailbox_cleaner')

    def test_get_tags(self):
        """Testing flag extraction."""

        INPUT=[(b'1 (RFC822 {242020}', b'\r\n'), b' UID 142377 FLAGS (\\Seen \\Recent NotJunk)']
        OUTPUT=MailboxCleaner.get_flags_from_struct(INPUT)
        print("Result: ", OUTPUT)
        self.assertTrue("Seen" in OUTPUT)
        self.assertTrue("NotJunk" in OUTPUT)
        self.assertFalse("Recent" in OUTPUT)

    def test_convert_date(self):
        """Testing date conversion."""

        INPUT="Thu, 22 Oct 2020 12:38:26 +0200"
        OUTPUT=MailboxCleaner.convert_date(INPUT)
        EXPECTED='"22-Oct-2020 12:38:26 +0200"'
        print("Result: ", OUTPUT)
        self.assertEqual(OUTPUT, EXPECTED)

    def test_convert_filename(self):
        """Testing decoding filenames."""

        INPUT="=?iso-8859-1?Q?2018-02-21=5FRegierender_B=FCrgermeister=5F_in_Ber?= =?iso-8859-1?Q?lin.pdf?="
        OUTPUT=MailboxCleaner.convert_filename(INPUT)
        EXPECTED='2018-02-21_Regierender Bürgermeister_ in Berlin.pdf'
        print("Result: ", OUTPUT)
        self.assertEqual(OUTPUT, EXPECTED)        

        INPUT="file/with/slash.pdf"
        OUTPUT=MailboxCleaner.convert_filename(INPUT)
        EXPECTED='file_with_slash.pdf'
        print("Result: ", OUTPUT)
        self.assertEqual(OUTPUT, EXPECTED)        

    def test_detach_attachment(self):
        """Testing detaching attachments."""

        INPUT='tests/test.eml'
        EXPECTED='removed-fed00c051c9f991a8a2d19dcadcf5ff3.jpg.txt'

        with open(INPUT) as fp:
            msg = email.message_from_file(fp)

        self.assertFalse(EXPECTED in msg.as_string())
        e = MailboxCleaner(self.args)
        modified = e.download_and_detach_attachments(msg)
        self.assertTrue(modified)
        self.assertTrue(EXPECTED in msg.as_string())
        modified = e.download_and_detach_attachments(msg)
        self.assertFalse(modified)

if __name__ == '__main__':
    unittest.main()
