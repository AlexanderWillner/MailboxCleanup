# Download and Remove Attachments from E-Mails

This module can be used to download and to strip / detach / remove attachments from e-mails on IMAP servers.

![GitHub CodeQL](https://github.com/AlexanderWillner/MailboxCleanup/workflows/CodeQL/badge.svg)
[![GitHub Build](https://github.com/AlexanderWillner/MailboxCleanup/workflows/Build-Test/badge.svg)](https://github.com/AlexanderWillner/MailboxCleanup/actions?query=workflow%3ABuild-Test)
[![Travis Build](https://travis-ci.org/AlexanderWillner/MailboxCleanup.svg?branch=main)](https://travis-ci.org/AlexanderWillner/MailboxCleanup)
[![Scrutinizer Build](https://scrutinizer-ci.com/g/AlexanderWillner/MailboxCleanup/badges/build.png?b=main)](https://scrutinizer-ci.com/g/AlexanderWillner/MailboxCleanup/build-status/main)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/AlexanderWillner/MailboxCleanup/badges/quality-score.png?b=main)](https://scrutinizer-ci.com/g/AlexanderWillner/MailboxCleanup/?branch=main)
[![Code Inspector QA](https://www.code-inspector.com/project/15204/status/svg)](https://frontend.code-inspector.com/)
[![Coveralls Coverage](https://coveralls.io/repos/github/AlexanderWillner/MailboxCleanup/badge.svg)](https://coveralls.io/github/AlexanderWillner/MailboxCleanup)

## Abstract

We all receive dozens and hundreds of new e-mail messages every day. Some of them even contain large attachments. The storage capacity on servers, however, are often limited. Deleting entire e-mails is often not an option, removing single attachments manually is time consuming and storing file locally is not optimal. With this script you can iterate over all e-mails in your inbox or within all folders, download the attachments locally and remove the attachments from the e-mails remotely. The script has been tested with Google Mail and Exchange servers with tens of thousands of e-mails and extracted thousands of attachments / multiple gigabytes in this process. As a result it is now possible to archive e-mails from many, many years on IMAP servers without exceeding mail server space limitations. Contributions and feedback are always welcome.

## Usage

You can run the command via `./bin/mailbox_cleaner`.

```shell
$ ./bin/mailbox_cleaner --help
usage: mailbox_cleaner.py [-h] [-a] [-d] [-k] [-c] [-r] [-m MAX_SIZE] [-f FOLDER] [-l UPLOAD] [-t TARGET] -s SERVER -u USER [-o PORT] -p PASSWORD [-v] [--version]

optional arguments:
  -h, --help            show this help message and exit
  -a, --all             iterate over all folders
  -d, --detach          remove attachments
  -k, --skip-download   don't download attachments
  -c, --reset-cache     reset cache
  -r, --read-only       read-only mode for the imap server
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

Some useful tips:

- Using the password from a keychain: If you don't want to type your password on the terminal, you can use built-in password managing tools (here an example using the macOS Keychain): `--password $(security -q find-generic-password -wa googlemailpwd)`.
- Enable debug and read-only mode: To make sure nothing changes on your server while you're testing, use the flag `--read-only` and enabled the debug mode via `-vvv` to understand what is happening.
- Download large attachments: By default, the application just downloads large attachments to the folder `attachments` and you might want to do this with all your mails using `--all`.
- Remove large attachments from server: To safe space on the mail server, you might want to remove mail attachments from the server: `$ ./bin/mailbox_cleaner --detach`.
- Upload messages to the server: You might have a large archive of mails (`eml`, `emlx` and `partial.emlx` files) that you want to detach the large attachements from and then upload the small text parts: `$ ./bin/mailbox_cleaner  --upload path/to/archive --folder import`.

### Example

```shell
$  ./bin/mailbox_cleaner --server imap.google.de --user user@example.org --password mypass --folder temp --max-size 20 --detach -vvv
Read Only	: False
Detach		: True
Cache Enabled	: True
Download	: True
Max Size	: 20 KB
Target		: attachments
Upload		: None
All Folders	: False
Folders (#)	: OK (32)
Progress	: 1 / 1 (folders)
Folder		: temp (started)
Mails (#)	: OK (4)
Progress	: 1 / 4 (mail uid: 96)
  Result (Size)	: OK (40 KB)
  Flags		: \Seen
  Subject	: Test1
    Part	: 39 KB / 20 KB (type: multipart)
    Part	: 1 KB / 20 KB (type: multipart)
    Part	: 0 KB / 20 KB (type: text)
    Part	: 0 KB / 20 KB (type: text)
    Part	: 37 KB / 20 KB (type: image)
      Downl.	: "fed00c051c9f991a8a2d19dcadcf5ff3.jpg" (image)
      Downl.	: To "/var/folders/q6/nhd43_qx2jv9dq75dk6c5fy40000gn/T/tmp5xtsr7yb"
      Moving	: From "/var/folders/q6/nhd43_qx2jv9dq75dk6c5fy40000gn/T/tmp5xtsr7yb" to "attachments/fed00c051c9f991a8a2d19dcadcf5ff3.jpg".
      Detaching	: fed00c051c9f991a8a2d19dcadcf5ff3.jpg
    Uploading	: "24-Oct-2020 09:26:57 +0200" / \Seen
    Success	: OK
    Deleting	: ('OK', [b'1 (FLAGS (\\Seen \\Deleted))'])
    Comment	: Expunged
Progress	: 2 / 4 (mail uid: 97)
  Result (Size)	: OK (40 KB)
  Flags		: \Seen
  Subject	: Test2
    Part	: 39 KB / 20 KB (type: multipart)
    Part	: 1 KB / 20 KB (type: multipart)
    Part	: 0 KB / 20 KB (type: text)
    Part	: 0 KB / 20 KB (type: text)
    Part	: 37 KB / 20 KB (type: image)
      Downl.	: "fed00c051c9f991a8a2d19dcadcf5ff3.jpg" (image)
      Downl.	: To "/var/folders/q6/nhd43_qx2jv9dq75dk6c5fy40000gn/T/tmp3_njbppc"
      Moving	: From "/var/folders/q6/nhd43_qx2jv9dq75dk6c5fy40000gn/T/tmp3_njbppc" to "attachments/fed00c051c9f991a8a2d19dcadcf5ff3.jpg".
      Conflict	: Resolving same file / other hash...
      Detaching	: fed00c051c9f991a8a2d19dcadcf5ff3.jpg
    Uploading	: "25-Oct-2020 08:26:57 +0100" / \Seen
    Success	: OK
    Deleting	: ('OK', [b'1 (FLAGS (\\Seen \\Deleted))'])
    Comment	: Expunged
Progress	: 3 / 4 (mail uid: 98)
  Result (Size)	: OK (40 KB)
  Flags		: \Seen
  Subject	: Test3
    Part	: 39 KB / 20 KB (type: multipart)
    Part	: 1 KB / 20 KB (type: multipart)
    Part	: 0 KB / 20 KB (type: text)
    Part	: 0 KB / 20 KB (type: text)
    Part	: 37 KB / 20 KB (type: image)
Warning	: Unknown attachment (skipping this attachment)
Progress	: 4 / 4 (mail uid: 99)
  Result (Size)	: OK (39 KB)
  Flags		: \Seen
  Subject	: Test4
    Part	: 38 KB / 20 KB (type: multipart)
    Part	: 0 KB / 20 KB (type: text)
    Part	: 37 KB / 20 KB (type: image)
      Downl.	: "page-icon.jpg" (image)
      Downl.	: To "/var/folders/q6/nhd43_qx2jv9dq75dk6c5fy40000gn/T/tmpet2j30gj"
      Moving	: From "/var/folders/q6/nhd43_qx2jv9dq75dk6c5fy40000gn/T/tmpet2j30gj" to "attachments/page-icon.jpg".
      Detaching	: page-icon.jpg
    Uploading	: "27-Oct-2020 08:26:57 +0100" / \Seen
    Success	: OK
    Deleting	: ('OK', [b'2 (FLAGS (\\Seen \\Deleted))'])
    Comment	: Expunged
Folder		: temp (completed)
Connection	: Closed
Connection	: Logged Out
```



## Open Issues / Planned Enhancements

* Enhance error handling. E.g. detect silent Exchange errors such as a successful fetch of mails with a localized subject such as `Fehler beim Abrufen der folgenden Nachricht`).
* Filter specific attachements. E.g. don't download `smime.p7m`.

