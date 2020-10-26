# Download and Remove Attachments from E-Mails

This module can be used to download and to strip / detach / remove attachments from e-mails on IMAP servers.

![GitHub CodeQL](https://github.com/AlexanderWillner/MailboxCleanup/workflows/CodeQL/badge.svg)
[![GitHub Build](https://github.com/AlexanderWillner/MailboxCleanup/workflows/Build-Test/badge.svg)](https://github.com/AlexanderWillner/MailboxCleanup/actions?query=workflow%3ABuild-Test)
[![Travis Build](https://travis-ci.org/AlexanderWillner/MailboxCleanup.svg?branch=main)](https://travis-ci.org/AlexanderWillner/MailboxCleanup)
[![Scrutinizer Build](https://scrutinizer-ci.com/g/AlexanderWillner/MailboxCleanup/badges/build.png?b=main)](https://scrutinizer-ci.com/g/AlexanderWillner/MailboxCleanup/build-status/main)
[![Scrutinizer QA](https://scrutinizer-ci.com/g/AlexanderWillner/MailboxCleanup/badges/code-intelligence.svg?b=main)](https://scrutinizer-ci.com/code-intelligence)
[![Code Inspector QA](https://www.code-inspector.com/project/15204/status/svg)](https://frontend.code-inspector.com/)
[![Coveralls Coverage](https://coveralls.io/repos/github/AlexanderWillner/MailboxCleanup/badge.svg)](https://coveralls.io/github/AlexanderWillner/MailboxCleanup)

## Abstract

We all receive dozens and hundreds of new e-mail messages every day. Some of them even contain large attachments. The storage capacity on servers, however, are often limited. Deleting entire e-mails is often not an option, removing single attachments manually is time consuming and storing file locally is not optimal. With this script you can iterate over all e-mails in your inbox or within all folders, download the attachments locally and remove the attachments from the e-mails remotely. The script has been tested with Google Mail and Exchange servers with tens of thousands of e-mails and extracted thousands of attachments / multiple gigabytes in this process. As a result it is now possible to archive e-mails from many, many years on IMAP servers without exceeding mail server space limitations. Contributions and feedback are always welcome.

## Usage

You can run the command via `./bin/mailbox_cleaner`.

```shell
$ ./bin/mailbox_cleaner --help
usage: mailbox_cleaner.py [-h] [-a] [-d] [-k] [-r] [-m MAX_SIZE] [-f FOLDER] [-l UPLOAD] [-t TARGET] -s SERVER -u USER [-o PORT] -p PASSWORD [-v] [--version]

optional arguments:
  -h, --help            show this help message and exit
  -a, --all             iterate over all folders
  -d, --detach          remove attachments
  -k, --skip-download   download attachments
  -r, --reset-cache     reset cache
  -m MAX_SIZE, --max-size MAX_SIZE
                        max attachment size in KB
  -f FOLDER, --folder FOLDER
                        imap folder to process
  -l UPLOAD, --upload UPLOAD
                        local folder with messages to upload
  -t TARGET, --target TARGET
                        download attachments to this local folder
  -s SERVER, --server SERVER
                        imap server
  -u USER, --user USER  imap user
  -o PORT, --port PORT  imap port
  -p PASSWORD, --password PASSWORD
                        imap user
  -v, --verbose         be more verbose (-v, -vv)
  --version             show program's version number and exit
```

## Example

If you don't want to type your password on the terminal, you can use built-in password managing tools (here an example using the macOS Keychain).

```shell
$ ./bin/mailbox_cleaner --server imap.gmail.com --user user@example.org --password $(security -q find-generic-password -wa googlemailpwd)
Folders (#) : OK (27)
All Folders : False
Folder      : Inbox (started)
Read Only   : True
Mails (#)   : OK (30)
Folder      : Inbox (completed)
```

You can also remove attachments from local `eml` files from a directory and upload them:

```shell
$ ./bin/mailbox_cleaner --server imap.gmail.com --user user@example.org --password $(security -q find-generic-password -wa googlemailpwd) --folder imap_folder --upload my_eml_dir
Folders (#) : OK (27)
All Folders : False
File        : my_eml_dir/test.eml (Test)
    Success : OK
```

## Open Issues / Planned Enhancements

* Enhance error handling. E.g. detect silent Exchange errors such as a successful fetch of mails with a localized subject such as `Fehler beim Abrufen der folgenden Nachricht`).
* Filter specific attachements. E.g. don't download `smime.p7m`.
