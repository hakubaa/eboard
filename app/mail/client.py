import imaplib
import socket
import re


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
        self, id, *, fields=["Subject", "Date", "From"], uid=False
    ): 
        fetch_status, data = self.mail.fetch()
        return [dict(map(lambda x: (x, self._find_subject(data[0][1], x)), fields))]


    def get_body(self, id): pass


    def get_email(self, id): pass


    def _find_subject(self, text, field, *, ignorecase=True, encoding="utf-8"): 
        if isinstance(text, bytes):
            text = text.decode(encoding)
        pattern = re.compile("%s: (?P<subject>.*)\r\n" % field,
                             flags = re.IGNORECASE if ignorecase else 0)
        match = pattern.search(text)
        return match.group("subject") if match else None