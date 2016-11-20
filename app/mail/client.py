import imaplib
import socket
import collections
import re
from email.parser import HeaderParser


class ImapClient:
    '''
    Wraps imaplib.IMAP4_SSL and provides additional high-level methods for
    accessing messages.
    '''
    def __init__(self, addr, timeout=None):
        socket.setdefaulttimeout(timeout)
        self.mail = imaplib.IMAP4_SSL(addr)

    def __getattr__(self, attr):
        '''
        Delagate references to undefined attributes in instance to
        imaplib.IMAP4_SSL.
        '''
        if attr in dir(self.mail):
            return getattr(self.mail, attr)
        raise AttributeError("'%s' object has not attribute '%s'" % 
                             (self.__class__.__name__, attr))

    def list_mailbox(self, mailbox="INBOX", *criteria, uid=False):
        '''
        Returns the list of e-mails (ids or uids) from selected mailbox. 
        Accepts additional criteria which are passed to search method. 
        '''
        select_status, msg = self.mail.select(mailbox)
        if select_status == "OK":
            if uid:
                search_status, data = self.uid(
                    "search", None, *criteria or ("ALL",)
                )
            else:
                search_status, data = self.mail.search(
                    None, *criteria or ("ALL",)
                )
            if search_status == "OK":
                return (search_status, data[0].split())
            else:
                return (search_status, data)
        else:
            return (select_status, msg)

    def get_header(
        self, ids, *, fields=None, uid=False
    ): 
        headers = list()

        if isinstance(ids, bytes):
            ids_bytes = ids
        elif isinstance(ids, str):
            ids_bytes = bytes(ids, "utf-8")
        elif isinstance(ids, collections.Iterable):
            ids_bytes = b','.join(item if isinstance(item, bytes) 
                                  else bytes(str(item), "utf-8") for item in ids)
        else: # assume ids is a number
            ids_bytes = bytes(str(ids), "utf-8")

        parser = HeaderParser()

        if fields:
            msg_parts = "BODY.PEEK[HEADER.FIELDS (%s)]" % " ".join(fields)
        else:
            msg_parts = "BODY.PEEK[HEADER]"

        if uid:
            fetch_status, data = self.mail.uid("fetch", ids_bytes, msg_parts)
        else:
            fetch_status, data = self.mail.fetch(ids_bytes, msg_parts)

        if fetch_status == "OK":
            for item in data:
                if item == b')': continue   
                assert len(item) == 2, "Unexpected number of items in fetch response." 
                
                # Find message'id
                if uid:
                    pattern = re.compile(".*UID (?P<id>\d+)")
                else:
                    pattern = re.compile("(?P<id>\d+)")
                match = pattern.search(item[0].decode("utf-8"))

                header = dict(parser.parsestr(item[1].decode()))
                header["id"] = int(match.group("id")) if match else None
                headers.append(header)

            return ("OK", headers)
        else:
            return (fetch_status, data)

    def get_body(self, id): pass


    def get_email(self, id): pass