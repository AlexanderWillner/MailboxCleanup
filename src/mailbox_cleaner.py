#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module to download and to detach/strip/remove attachments
from e-mails on IMAP servers.
"""

from __future__ import print_function
import email
import email.utils
import email.mime.text
import tempfile
import shutil
import time
import re
import unicodedata
import hashlib
import typing
import os.path
import socket
import pickle
import argparse
import logging
import collections
import imaplib
imaplib._MAXLINE = 10000000  # pylint: disable=protected-access

__author__ = "Alexander Willner"
__copyright__ = "Copyright 2020, Alexander Willner"
__credits__ = ["github.com/guido4000",
               "github.com/halteproblem", "github.com/jamesridgway"]
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Alexander Willner"
__email__ = "alex@willner.ws"
__status__ = "Development"


class MailboxCleaner():
    """
    Download and detach/strip/remove attachments from e-mails
    on IMAP servers.
    """

    __RETRIES = 2

    __PREFIXES = ('Contacts', 'Calendar', '"Calendar',
                  'Trash', '"Deleted', 'Tasks',
                  '"[Gmail]"')

    __PLACEHOLDER = """
===========================================================
This message contained an attachment that was stripped out.
The filename was: "%(filename)s".
The size was: %(size)d KB.
The type was: %(type)s.
Tool: https://github.com/AlexanderWillner/MailboxCleanup
===========================================================
"""

    def __init__(self, args):
        self.cache = collections.OrderedDict()
        self.args = args
        self.cache_file = args.server + '_cache.pkl'
        self.readonly = not self.args.detach
        self.imap: imaplib.IMAP4_SSL = None

    def run(self):
        """Login and process mails."""
        try:
            self.login()
            self.__load_cache()
            folders = self.get_folders_from_server()
            self.process_folders(folders)
            self.logout()
        except KeyboardInterrupt as error:
            raise SystemExit('\nCancelling...') from error
        finally:
            self.__save_cache()

    def __load_cache(self):
        """Load cache of processed mail UIDs with their subjects."""

        # Create new cache if needed
        if not os.path.exists(self.cache_file) or\
           self.args.reset_cache:
            self.__save_cache()

        with open(self.cache_file, 'rb') as filepointer:
            self.cache = pickle.load(filepointer)

    def __save_cache(self):
        """Save cache of processed mail UIDs with their subjects."""

        with open(self.cache_file, 'wb+') as filepointer:
            pickle.dump(self.cache, filepointer, pickle.HIGHEST_PROTOCOL)

    def login(self):
        """Log into the IMAP server."""

        try:
            self.imap = imaplib.IMAP4_SSL(self.args.server)
            self.imap.login(self.args.user, self.args.password)
        except socket.gaierror as error:
            raise SystemExit('Login failed (wrong server?): %s' %
                             error) from error
        except imaplib.IMAP4.error as error:
            raise SystemExit('Login failed (wrong password?): %s' %
                             error) from error

    def logout(self):
        """Log out of the IMAP server."""

        self.imap.close()
        self.imap.logout()

    def process_folders(self, folders):
        """Iterate over mails in given folders."""

        # Iterate over each folder
        for i, folder in enumerate(folders, start=1):

            # Get all mails in this folder
            logging.info('Progress\t: %s / %s (folders)', i, len(folders))
            logging.warning('Folder\t\t: %s (started)', folder)
            msg_uids = self.get_msgs_from_server_folder(folder)

            # Iterate over each email
            for j, msg_uid in enumerate(msg_uids, start=1):

                # Skip if already in cache
                logging.info('Progress\t: %s / %s (mail uid: %s)',
                             j, len(msg_uids), msg_uid.decode())
                if msg_uid in self.cache:
                    logging.info('  Subject\t: %s (cached)',
                                 self.cache[msg_uid])
                    continue

                # Get the actual email
                msg, msg_flags = self.get_msg_from_server(msg_uid)
                subject = self.get_subject(msg)
                logging.info('  Subject\t: %s', subject)

                # Download and detach attachments from email
                modified = self.download_and_detach_attachments(msg)

                # Upload new email
                if modified:
                    self.upload_msg_to_server(msg, msg_flags, folder, msg_uid)

                self.cache[msg_uid] = subject

            logging.warning('Folder\t\t: %s (completed)', folder)

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

    def upload_msg_to_server(self, msg, msg_flags, folder, msg_uid):
        """Replace old/large message on the server."""

        # Only upload in non-readonly mode
        if self.readonly:
            logging.debug('    Detaching\t: skipped (read-only mode)')
            return

        # Knowing what's going on
        msg_date = self.convert_date(msg.get('date'))
        logging.debug('    Uploading\t: %s / %s', msg_date, msg_flags)

        # Upload new message and delete the old one
        status, data = self.imap.append(
            folder, msg_flags, msg_date, msg.as_string().encode())
        if status == 'OK':
            self.imap.uid('STORE', msg_uid, '+FLAGS', '\\Deleted')
            # GMail needs special treatment
            try:
                self.imap.uid('STORE', msg_uid, '+X-GM-LABELS', '\\Trash')
            except imaplib.IMAP4.error:
                pass
            self.imap.expunge()
        else:
            logging.warning('    Error\t: "%s"', data)

    def is_non_detachable_part(self, part):
        """Only process certain types and sizes of attachments."""

        msg_size = len(str(part)) / 1024
        logging.debug('    Part\t: %d KB / %d KB (type: %s)',
                      msg_size, self.args.max_size,
                      part.get_content_maintype())

        return part.get_content_maintype() == 'multipart' or \
            part.get('Content-Disposition') is None or \
            msg_size <= self.args.max_size

    def get_msg_from_server(self, uid):
        """Fetch an email from the IMAP server."""

        # Sometimes IMAP servers might return empty bodies, so try again
        for _ in range(self.__RETRIES):
            try:
                result, data = self.imap.uid('fetch', uid,
                                             '(UID BODY.PEEK[] FLAGS)')
                if data is None or data[0] is None:
                    logging.warning('  Error\t: '
                                    'Could not get a message body. '
                                    'Retrying in a few seconds...')
                    time.sleep(2)
                    raise imaplib.IMAP4.error('Could not get a message body')

                body = data[0][1]
                logging.debug('  Result (Size)\t: %s (%d KB)',
                              result, len(body) / 1024)

                msg = self.get_mail_from_struct(data)
                msg_flags = self.get_flags_from_struct(data)

                logging.debug('  Flags\t\t: %s', msg_flags)

                return (msg, msg_flags)
            except imaplib.IMAP4.error:
                continue
            break
        else:
            raise imaplib.IMAP4.error('Could not get a message subject')

    def get_msgs_from_server_folder(self, folder):
        """Get all emails from a folder on the IMAP server."""

        # Safety net: enable read-only if requested
        logging.warning('Read Only\t: %s', self.readonly)
        self.imap.select(folder, readonly=self.readonly)

        # Extract email UIDs
        result_mails, data_mails = self.imap.uid('search', None, "ALL")
        msg_uids = data_mails[0].split()
        logging.warning('Mails (#)\t: %s (%s)',
                        result_mails, len(msg_uids))

        return msg_uids

    def get_folders_from_server(self) -> typing.List[str]:
        """Get the folders from the IMAP server to iterate through."""

        res, folder_list = self.imap.list()

        logging.warning('Folders (#)\t: %s (%s)', res, len(folder_list))
        logging.warning('All Folders\t: %s', self.args.all)

        if not self.args.all:
            folders = [self.args.folder]
        else:
            folders = [item.decode().split('"/"')[-1].strip()
                       for item in folder_list]

            folders[:] = [item for item in folders
                          if not item.startswith(self.__PREFIXES)]
            folders[:] = [item for item in folders
                          if not item.startswith(self.__PREFIXES)]

        return folders

    def download_attachment(self, part) -> bool:
        """Download the attachment from a part of an email."""

        if self.args.skip_download:
            logging.info('    Downloading\t: skipped (disabled)')
            return True

        if part.get_filename() is None:
            logging.warning('Warning\t: Could not download attachment '
                            '(skipping this attachment)')
            return False

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
            if payload is not None:
                file_temp.write(payload)
                self.copy_file(file_temp.name, file_attached)
            else:
                logging.warning('    Downloading\t: File "%s" was empty',
                                file_attached)

        return True

    def copy_file(self, source, target_name, iterator=0):
        """Copy file, check for duplicates via hash value."""

        target_base, target_extension = os.path.splitext(target_name)
        if iterator > 0:
            target_base = target_base + "-" + str(iterator)
        target = os.path.join(self.args.target, target_base + target_extension)
        logging.debug('    Moving\t: From "%s" to "%s".', source, target)

        if not os.path.isfile(target):
            shutil.copy2(source, target)
        else:
            source_hash = self.get_hash(source)
            target_hash = self.get_hash(target)
            if source_hash != target_hash:
                logging.debug(
                    '    Conflict\t: Same file with other hash (%s vs %s).',
                    source_hash, target_hash)
                self.copy_file(source, target_name, iterator + 1)
            else:
                logging.debug('    Moving\t: Already exists (skipping)')

    def detach_attachment(self, msg):
        """Replace large attachment with dummy text."""

        # Get message details
        msg_content = msg.get_content_type()
        msg_filename = self.convert_filename(msg.get_filename())
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
        msg_placeholder = self.__PLACEHOLDER % msg_details
        msg_placeholder = email.mime.text.MIMEText(msg_placeholder,
                                                   'text', 'utf-8')
        msg.set_payload(msg_placeholder.get_payload())

    @staticmethod
    def get_mail_from_struct(data) -> str:
        """Convert message to a string."""

        try:
            raw_email = (data[0][1]).decode('utf-8')
        except ValueError:
            try:
                raw_email = (data[0][1]).decode('iso-8859-1')
            except ValueError:
                raw_email = (data[0][1]).decode('utf-8', 'backslashreplace')

        return email.message_from_string(raw_email)

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
    def convert_date(date):
        """Convert dates to copy old date to new message."""

        pz_time = email.utils.parsedate_tz(date)
        stamp = email.utils.mktime_tz(pz_time)
        date = imaplib.Time2Internaldate(stamp)
        return date

    @staticmethod
    def get_flags_from_struct(data):
        """Get flags to copy old flags to new message."""

        flags = imaplib.ParseFlags(data[1])
        flags = b" ".join(flags) if flags != () else b""
        flags = flags.decode("utf-8")
        flags = flags.replace("\\Recent", "")  # read-only attribute
        return flags.strip()

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

        return MailboxCleaner.slugify_filename(filename)


def handle_arguments() -> argparse.ArgumentParser:
    """Provide CLI handler for application."""

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--all",
                        help="iterate over all folders", action='store_true')
    parser.add_argument("-d", "--detach",
                        help="remove attachments", action='store_true')
    parser.add_argument("-k", "--skip-download",
                        help="download attachments", action='store_true')
    parser.add_argument("-r", "--reset-cache",
                        help="reset cache", action='store_true')
    parser.add_argument("-m", "--max-size",
                        help="max attachment size in KB", default=200)
    parser.add_argument("-f", "--folder",
                        help="imap folder to process", default="Inbox")
    parser.add_argument("-t", "--target",
                        help="download attachments to this local folder",
                        default="attachments")
    parser.add_argument("-s", "--server", help="imap server", required=True)
    parser.add_argument("-u", "--user", help="imap user", required=True)
    parser.add_argument("-p", "--password", help="imap user", required=True)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbosity",
        help="be more verbose (-v, -vv)")
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING - args.verbosity * 10,
                        format="%(message)s")

    return args


def main():
    """Setup and run remover."""

    args = handle_arguments()
    remover = MailboxCleaner(args)
    remover.run()


if __name__ == '__main__':
    main()
