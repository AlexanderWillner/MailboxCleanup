#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Compatible with python3 and python2 (tested with at least 2.4)

# flake8: noqa
# pylint: skip-file
# Originally from https://github.com/LRGH/emlx2eml

import sys
import os
import logging
import struct
import email
import base64
import mimetypes

log = logging.getLogger("emlx2eml")
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(levelname)-5s: %(message)s"))
log.addHandler(console_handler)
log.setLevel(logging.DEBUG)
# log.setLevel(logging.ERROR)


def find_emlx(input):
    if os.path.islink(input):
        return []
    elif os.path.isdir(input):
        files = []
        for x in os.listdir(input):
            files += find_emlx(os.path.join(input, x))
        return files
    elif input.endswith(".emlx"):
        return [input]
    else:
        return []


# Some definitions, to enforce compatibility with python2 and python3
newline = struct.pack("B", 10)
if sys.version_info[0] == 2:
    message_from_bytes = email.message_from_string
    def message_as_bytes(msg): return msg.as_string(unixfrom=True)
else:
    message_from_bytes = email.message_from_bytes
    def message_as_bytes(msg): return msg.as_bytes(unixfrom=True)


def copy_emlx(emlx, out_dir):
    # Get the numeric id
    id = get_numeric_id(emlx)

    # Create output file
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    eml = os.path.join(out_dir, id+".eml")
    log.debug("Extract %s to %s", emlx, eml)
    if os.path.exists(eml):
        log.error("%s already exists", eml)
        return False
    # Parse the EMLX file
    msg = parse_emlx(emlx)
    msg.set_unixfrom("From emlx2eml Thu Apr 19 00:00:00 2012")
    # TODO: generate relevant values for unixfrom
    open(eml, "wb").write(message_as_bytes(msg))


def get_numeric_id(filename):
    id = os.path.basename(filename)
    assert(id.endswith(".emlx"))
    id = id[:-5]
    if id.endswith(".partial"):
        id = id[:-8]
    return id


def parse_emlx(filename):
    # Read file
    content = open(filename, "rb").read()

    # Extract parts
    eol = content.find(newline)
    length = int(content[:eol])
    body = content[eol+1:eol+1+length]
    # TODO: parse the content of 'plist', e.g. using plistlib
    # plist = content[eol+1+length:]
    msg = message_from_bytes(body)

    # Find where attachments may be
    id = get_numeric_id(filename)
    attach_dir = os.path.dirname(filename)
    if attach_dir == "":
        attach_dir = "."
    attach_dir += "/../Attachments/" + id

    # Make complete eml
    parse_msg(attach_dir, msg, [])
    return msg


def parse_msg(attach_dir, msg, depth):
    log.debug("%sPART %s %r of type %s", " "*len(depth),
              ".".join([str(_+1) for _ in depth]), msg, msg.get_content_type())
    if msg.is_multipart():
        for idx, part in enumerate(msg.get_payload()):
            parse_msg(attach_dir, part, depth+[idx])
            include_attachment(attach_dir, part, depth+[idx])


# When the attachment has no explicit filename, Mail.app generates a name
# which we want to guess.
base_filename = u"Mail Attachment"
mimetypes.add_type('image/pjpeg', '.jpg', strict=True)
mimetypes.add_type('image/jpg', '.jpg', strict=True)


def include_attachment(attach_dir, part, depth):
    if "X-Apple-Content-Length" not in part:
        return
    file = part.get_filename()
    mime_type = part.get_content_type()
    if file is None:
        file = base_filename + mimetypes.guess_extension(mime_type)
    dirpath = attach_dir + "/" + ".".join([str(_+1) for _ in depth])
    try:
        data = open(dirpath+"/"+file, "rb").read()
    except FileNotFoundError:
        log.error("%s  Attachment '%s' not found in %s",
                  " "*len(depth), file, dirpath)
        return
    log.debug("%s  Attachment '%s' found", " "*len(depth), file)
    cte = part["Content-Transfer-Encoding"]
    if cte is None:
        pass
    elif cte == "base64":
        data = base64.b64encode(data)
        data = newline.join([data[i*76:(i+1)*76]
                             for i in range(len(data)//76+1)])
    else:
        log.error("Attachment dir is %s", attach_dir)
        log.error("  CTE %r", cte)
        log.error("  CD  %r", part["Content-Disposition"])
    part.set_payload(data)


if __name__ == "__main__":
    try:
        input, out_dir = sys.argv[1:]
    except ValueError:
        print("Syntax: emlx2eml.py <source> <output_dir>")
        print("    <source> can be an EMLX file, or a directory that will")
        print("    be recursively searched for EMLX files.")
        sys.exit(1)
    log.debug("Input %s; Output %s", input, out_dir)
    for emlx in find_emlx(input):
        copy_emlx(emlx, out_dir)
