#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module to download and to detach/strip/remove attachments
from e-mails on IMAP servers.
"""

from __future__ import print_function

import re
import email
import email.mime.text
import email.utils
import email.parser
import imaplib
import logging
import socket
import time
import typing
import collections
import os.path
import pickle

from src.mailbox_message import MailboxCleanerMessage

imaplib._MAXLINE = 10000000  # pylint: disable=protected-access


__author__ = "Alexander Willner"
__copyright__ = "Copyright 2020, Alexander Willner"
__credits__ = ["github.com/guido4000",
               "github.com/halteproblem", "github.com/jamesridgway"]
__license__ = "MIT"
__version__ = "1.0.4"
__maintainer__ = "Alexander Willner"
__email__ = "alex@willner.ws"
__status__ = "Development"


class MailboxCleanerIMAP():
    """
    Download and detach/strip/remove attachments from e-mails
    on IMAP servers.
    """

    # Number of retries to get messages
    __RETRIES = 2

    # IMAP folders to ignore
    __IGNORE_PREFIX = ('Contacts', 'Calendar', '"Calendar',
                       'Trash', '"Deleted', 'Tasks',
                       '"[Gmail]"')

    def __init__(self, args, imap=None):
        """Initialize class."""

        self.args = args
        self.message = MailboxCleanerMessage(args)
        self.cache = collections.OrderedDict()
        self.cache_file = os.path.join(
            self.args.target, '_cache-' + args.server + '.pkl')
        self.imap: imaplib.IMAP4_SSL = imap
        self.stopped: bool = False

    def cleanup(self):
        """Cleanup after error."""

        self._save_cache()

    def login(self):
        """Log into the IMAP server."""

        try:
            if self.imap is None:
                self.imap = imaplib.IMAP4_SSL(self.args.server)
            self.imap.login(self.args.user, self.args.password)
            self._load_cache()
        except socket.gaierror as error:
            raise SystemExit('Login failed (wrong server?): %s' %
                             error) from error
        except imaplib.IMAP4.error as error:
            raise SystemExit('Login failed (wrong password?): %s' %
                             error) from error

    def logout(self):
        """Log out of the IMAP server."""

        try:
            self.imap.close()
            logging.warning('Connection\t: Closed')
        except (AttributeError, imaplib.IMAP4.error):
            pass

        try:
            self.imap.logout()
            logging.warning('Connection\t: Logged Out')
        except (AttributeError, imaplib.IMAP4.error):
            pass

        self.imap = None

    def does_msg_exist(self, msg) -> bool:
        """Check if message is already on the server."""

        msg_uid = self.message.get_uid(msg)
        status, error = self.imap.select(self.args.folder, readonly=self.args.read_only)
        if status != "OK":
            raise imaplib.IMAP4.error('Could not select folder: %s' % error)
        status, data = self.imap.uid('SEARCH', None,
                                     '(HEADER Message-ID "%s") UNDELETED'
                                     % msg_uid)

        if data is not None and\
           len(data[0]) > 0 and\
           self.args.upload is not None:
            logging.warning('    Duplicate\t: %s', status)
            self.cache[msg_uid] = self.message.get_subject(msg_uid)
            return True

        return False

    def process_directory(self):
        """Iterate over mails from a local directory for upload."""
        self.message.process_directory(self.upload, cache=self.cache)

    def process_folders(self):  # noqa: C901
        """Iterate over mails in configured folders."""

        folders = self.get_folders()
        self.stopped = False

        # Iterate over each folder
        for i, folder in enumerate(folders, start=1):

            # For threaded environments
            if self.stopped:
                break

            # Get all mails in this folder
            if hasattr(self.args, 'logger'):
                self.args.logger.log_progress_folders(i, len(folders), folder)
            logging.info('Progress\t: %s / %s (folders)', i, len(folders))
            logging.warning('Folder\t\t: %s (started)', folder)
            msg_uids = self.get_msgs_from_folder(folder)

            # Iterate over each email
            for j, msg_uid in enumerate(msg_uids, start=1):

                # For threaded environments
                if self.stopped:
                    break

                # Skip if already in cache
                logging.info('Progress\t: %s / %s (mail uid: %s)',
                             j, len(msg_uids), msg_uid.decode())
                if msg_uid in self.cache:
                    logging.info('  Subject\t: %s (cached)',
                                 self.cache[msg_uid])
                    if hasattr(self.args, 'logger'):
                        self.args.logger.log_progress_mails(
                            j, len(msg_uids), self.cache[msg_uid])
                    continue

                # Get the actual email
                try:
                    msg, msg_flags = self.get_msg(msg_uid)
                except imaplib.IMAP4.error as error:
                    try:
                        logging.info(
                            '  Error\t\t: Message %s (%s). Logging in again.',
                            msg_uid, error)
                        self.logout()
                        self.login()
                        self.imap.select(folder, readonly=self.args.read_only)
                        msg, msg_flags = self.get_msg(msg_uid)
                    except imaplib.IMAP4.error:
                        logging.info('  Error\t: Message %s skipped', msg_uid)
                        continue

                subject = self.message.get_subject(msg)
                logging.info('  Subject\t: %s', subject)
                if hasattr(self.args, 'logger'):
                    self.args.logger.log_progress_mails(
                        j, len(msg_uids), subject)

                # Download and detach attachments from email
                modified = self.message.download_and_detach_attachments(msg)

                # Upload new email
                if modified:
                    self.replace_msg(msg, msg_flags, msg_uid, folder)

                self.cache[msg_uid] = subject
                if j % 10 == 0:
                    self._save_cache()

            logging.warning('Folder\t\t: %s (completed)', folder)

    def replace_msg(self, msg, msg_flags, msg_uid, folder):
        """Upload new message and remove the old one."""

        # Only upload in non-readonly mode
        if self.args.read_only:
            logging.debug('    Replacing\t: skipped (read-only)')
            return

        # Upload new message
        status, data = self.upload(msg, folder, msg_flags)

        # Delete old message
        if status == 'OK' and self.args.read_only is False:
            result = self.imap.select(folder, readonly=self.args.read_only)
            assert result[0] == 'OK'
            result = self.imap.uid('STORE', msg_uid, '+FLAGS', '\\Deleted')
            logging.debug('    Deleting\t: %s', result)
            # GMail needs special treatment
            try:
                self.imap.uid('STORE', msg_uid, '+X-GM-LABELS', '\\Trash')
            except imaplib.IMAP4.error:
                pass
            # Sometimes expunge just fails with an EOF socket error
            try:
                self.imap.expunge()
                logging.debug('    Comment\t: Expunged')
            except imaplib.IMAP4.abort:
                pass
        else:
            logging.warning('    Result\t: %s (%s)', status, data)

    def upload(self, msg, folder, msg_flags='\\Seen'):
        """Upload message to server."""

        # Knowing what's going on
        try:
            msg_date = self.convert_date(msg.get('date'))
            msg_subject = self.message.get_subject(msg)
            msg_uid = self.message.get_uid(msg)
        except TypeError as error:
            status = "Error"
            data = error
            logging.warning('    Error\t: %s, %s', status, data)
            return status, data

        if self.args.read_only:
            logging.warning('    Uploading\t: skipped (read-only)')
            return ('Read Only', '')

        # Check cache
        msg_uid = self.message.get_uid(msg)
        if msg_uid in self.cache:
            logging.warning('    Cache\t: OK')
            return ('Cached', '')

        # Check for duplicates
        if self.does_msg_exist(msg) is True:
            self.cache[msg_uid] = msg_subject
            return ('Duplicate', '')

        logging.debug('    Uploading\t: %s / %s', msg_date, msg_flags)

        try:
            status, data = self.imap.append(
                folder, msg_flags, msg_date, msg.as_string().encode())
            if status == "OK":
                logging.warning('    Success\t: %s', status)
                self.cache[msg_uid] = msg_subject
            else:
                logging.warning('    Error\t: %s, %s (in %s)', status, data, folder)
        except imaplib.IMAP4.abort as error:
            status = "Error"
            data = error
            self.logout()
            self.login()

        return status, data

    def get_msg(self, uid):
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

                msg = self.get_msg_from_struct(data)
                msg_flags = self.get_flags_from_struct(data)

                logging.debug('  Flags\t\t: %s', msg_flags)

                return (msg, msg_flags)
            except imaplib.IMAP4.error:
                continue
            break
        else:
            raise imaplib.IMAP4.error('Could not get a message subject')

    def get_msgs_from_folder(self, folder):
        """Get all emails from a folder on the IMAP server."""

        # Safety net: enable read-only if requested
        self.imap.select(folder, readonly=self.args.read_only)

        # Extract email UIDs
        result_mails, data_mails = self.imap.uid('search', None, "ALL")
        msg_uids = data_mails[0].split()
        logging.warning('Mails (#)\t: %s (%s)',
                        result_mails, len(msg_uids))

        return msg_uids

    def get_folders(self) -> typing.List[str]:
        """Get the folders from the IMAP server to iterate through."""

        res, folder_list = self.imap.list()
        logging.warning('Folders (#)\t: %s (%s)', res, len(folder_list))

        folders = [re.split('"."|"/"', item.decode())[-1].strip()
                   for item in folder_list]

        if not self.args.all:
            if self.args.folder.lower() not in map(str.lower, folders):
                raise imaplib.IMAP4.error(
                    'IMAP folder %s does not exist. Existing folders: %s'
                    % (self.args.folder, folders))
            folders = [self.args.folder]
        else:
            folders[:] = [item for item in folders
                          if not item.startswith(self.__IGNORE_PREFIX)]
            folders[:] = [item for item in folders
                          if not item.startswith(self.__IGNORE_PREFIX)]

        return folders

    @staticmethod
    def convert_date(date):
        """Convert dates to copy old date to new message."""

        pz_time = email.utils.parsedate_tz(date)
        stamp = email.utils.mktime_tz(pz_time)
        date = imaplib.Time2Internaldate(stamp)
        return date

    @staticmethod
    def get_msg_from_struct(data) -> str:
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
    def get_flags_from_struct(data):
        """Get flags to copy old flags to new message."""

        flags = imaplib.ParseFlags(data[1])
        flags = b" ".join(flags) if flags != () else b""
        flags = flags.decode("utf-8")
        flags = flags.replace("\\Recent", "")  # read-only attribute
        return flags.strip()

    def _load_cache(self):
        """Load cache of processed mail UIDs with their subjects."""

        # Create new cache if needed
        if not os.path.exists(self.cache_file) or\
           self.args.reset_cache:
            self._save_cache()

        with open(self.cache_file, 'rb') as filepointer:
            self.cache = pickle.load(filepointer)

    def _save_cache(self):
        """Save cache of processed mail UIDs with their subjects."""

        if not os.path.exists(os.path.dirname(self.cache_file)):
            os.mkdir(os.path.dirname(self.cache_file))
            print("Cache folder created")
        with open(self.cache_file, 'wb+') as filepointer:
            pickle.dump(self.cache, filepointer, pickle.HIGHEST_PROTOCOL)
