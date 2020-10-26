#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module to download and to detach/strip/remove attachments
from e-mails on IMAP servers.
"""

from __future__ import print_function

import email
import email.mime.text
import email.utils
from email.parser import HeaderParser
import hashlib
import logging
import os.path
import re
import shutil
import tempfile
import unicodedata
import emlx

# pylint: disable=R0801
__author__ = "Alexander Willner"
__copyright__ = "Copyright 2020, Alexander Willner"
__credits__ = ["github.com/guido4000",
               "github.com/halteproblem", "github.com/jamesridgway"]
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Alexander Willner"
__email__ = "alex@willner.ws"
__status__ = "Development"


class MailboxCleanerMessage():
    """
    Class to represent an e-mail.
    """

    _PLACEHOLDER = """
===========================================================
This message contained an attachment that was stripped out.
The filename was: "%(filename)s".
The size was: %(size)d KB.
The type was: %(type)s.
Tool: https://github.com/AlexanderWillner/MailboxCleanup
===========================================================
"""

    def __init__(self, args):
        self.args = args

    def download_and_detach_attachments(self, msg):
        """Download attachments and remove them from the mail."""

        modified = False

        # Iterate over each part of the email
        for part in msg.walk():
            if self.is_non_detachable_part(part):
                continue
            success = self.download_attachment(part)
            if success:
                self.detach_attachment(part)
                modified = True

        return modified

    def is_non_detachable_part(self, part):
        """Only process certain types and sizes of attachments."""

        msg_size = len(str(part)) / 1024
        logging.debug('    Part\t: %d KB / %d KB (type: %s)',
                      msg_size, self.args.max_size,
                      part.get_content_maintype())

        return part.get_content_maintype() == 'multipart' or \
            part.get('Content-Disposition') is None or \
            msg_size <= self.args.max_size

    def download_attachment(self, part) -> bool:
        """Download the attachment from a part of an email."""

        if self.args.skip_download:
            logging.info('    Downloading\t: skipped (disabled)')
            return True

        file_attached = self.convert_filename(part.get_filename())

        if file_attached == "unknown":
            logging.warning('Warning\t: Unknown attachment '
                            '(skipping this attachment)')
            return False

        if not os.path.exists(self.args.target):
            os.mkdir(self.args.target)
        with tempfile.NamedTemporaryFile() as file_temp:
            logging.info('    Downloading\t: "%s" (%s)',
                         file_attached, part.get_content_maintype())
            logging.debug('    Downloading\t: To "%s"', file_temp.name)
            payload = part.get_payload(decode=True)
            file_temp.write(payload)
            self._copy_file(file_temp.name, file_attached)

        return True

    def _copy_file(self, source, target_name, iterator=0):
        """Copy file, check for duplicates via hash value."""

        target_base, target_extension = os.path.splitext(target_name)
        if iterator > 0:
            target_base = target_base + "-" + str(iterator)
        target = os.path.join(self.args.target, target_base + target_extension)
        if iterator == 0:
            logging.debug('    Moving\t: From "%s" to "%s".', source, target)

        if not os.path.isfile(target):
            shutil.copy2(source, target)
        else:
            source_hash = MailboxCleanerMessage.get_hash(source)
            target_hash = MailboxCleanerMessage.get_hash(target)
            if source_hash != target_hash:
                if iterator == 0:
                    logging.debug(
                        '    Conflict\t: Resolving same file / other hash...')
                self._copy_file(source, target_name, iterator + 1)
            else:
                logging.debug('    Moving\t: Already exists (same hash)')

    def process_directory(self, handler):
        """Upload messages from a local directory."""

        directory = self.args.upload
        filenames = os.listdir(directory)

        for i, filename in enumerate(filenames, start=1):
            logging.warning('Progress\t: %d / %d', i, len(filenames))
            if not filename.lower().endswith(".eml") and\
               not filename.lower().endswith(".emlx"):
                continue

            filename = os.path.join(directory, filename)
            with open(filename) as filepointer:
                if filename.lower().endswith(".emlx"):
                    msg = emlx.read(filename)
                else:
                    msg = email.message_from_file(filepointer)
                msg_subject = self.get_subject(msg)
                logging.warning('    File\t: %s (%s)', filename, msg_subject)

                # Remove attachments
                self.download_and_detach_attachments(msg)

                # Post process message (e.g. upload or save it)
                handler(msg)

    @staticmethod
    def detach_attachment(msg):
        """Replace large attachment with dummy text."""

        # Get message details
        msg_content = msg.get_content_type()
        msg_filename = MailboxCleanerMessage.convert_filename(
            msg.get_filename())
        msg_size = len(str(msg)) / 1024
        msg_type = msg.get_content_disposition()

        # Remove some old headers
        del msg['Content-Transfer-Encoding']
        del msg['Content-Disposition']
        del msg['Content-Description']
        for k, _v in msg.get_params()[1:]:
            msg.del_param(k)

        # Make sure different clients visualize the removed content properly
        msg.set_type('text/plain')
        msg.set_charset('utf-8')
        if msg_type == 'attachment':
            msg.add_header('Content-Disposition', 'inline')
        else:
            msg.add_header('Content-Disposition', 'attachment',
                           filename='removed-%s.txt' % msg_filename)
            msg.add_header('Content-Description',
                           'removed-%s.txt' % msg_filename)

        # Replace content
        msg_details = dict(type=msg_content,
                           filename=msg_filename,
                           size=msg_size)
        msg_placeholder = MailboxCleanerMessage._PLACEHOLDER % msg_details
        msg_placeholder = email.mime.text.MIMEText(msg_placeholder,
                                                   'text', 'utf-8')
        msg.set_payload(msg_placeholder.get_payload())

    @staticmethod
    def get_uid(message) -> str:
        """Get UID of message."""

        parser = HeaderParser()
        header = parser.parsestr(message.as_string())
        uid = email.utils.parseaddr(header['message-id'])
        return uid[1]

    @staticmethod
    def get_subject(message) -> str:
        """Get shortened message subject for visualization."""

        if 'subject' in message:
            subject = message['subject']
        else:
            subject = "unknown"  # very rarely messages have no subject
        subject, encoding = email.header.decode_header(subject)[0]
        encoding = 'utf-8' if encoding is None else encoding
        subject = subject.decode(encoding, errors='replace')\
            if hasattr(subject, 'decode') else subject
        subject = subject[:75] + (subject[75:] and '...')
        subject = subject.replace('\r\n', '')
        subject = subject.replace('\t', ' ')

        return subject

    @staticmethod
    def get_hash(filename: str) -> str:
        """Get hash from filename to detect duplicates."""

        hash_value = hashlib.sha256()
        with open(filename, "rb") as file:
            for byte_block in iter(lambda: file.read(4096), b""):
                hash_value.update(byte_block)
        return hash_value.hexdigest()

    @staticmethod
    def slugify_filename(value):
        """Make sure attachments contain only valid characters."""

        value = str(value)
        value = unicodedata.normalize('NFKC', value)
        value = re.sub(r'[^.\w\s-]', '_', value)
        return value

    @staticmethod
    def convert_filename(file_struct) -> str:
        """Decode the name of some attachments."""

        filename = 'unknown'
        if file_struct is not None:
            file_struct = email.header.decode_header(file_struct)[0]
            encoding = file_struct[1]
            if encoding is not None:
                filename = file_struct[0].decode(encoding)
            else:
                filename = file_struct[0]

        return MailboxCleanerMessage.slugify_filename(filename)
