import imaplib
import socket
import collections
import re
import email
from email.header import decode_header
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

    def len_mailbox(self, mailbox="INBOX"):
        '''Returns number of messages in a mailbox'''
        select_status, data = self.mail.select(mailbox)
        if select_status == "OK":
            return "OK", int(data[0].decode("utf-8"))
        return select_status, data

    def _ids_to_bytes(self, ids):
        if isinstance(ids, bytes):
            ids_bytes = ids
        elif isinstance(ids, str):
            ids_bytes = bytes(ids.replace(" ", ""), "utf-8")
        elif isinstance(ids, collections.Iterable):
            ids_bytes = b','.join(item if isinstance(item, bytes) 
                                  else bytes(str(item), "utf-8") for item in ids)
        else: # assume ids is a number
            ids_bytes = bytes(str(ids), "utf-8")
        return ids_bytes

    def get_headers(
        self, ids, *, fields=None, uid=False
    ): 
        '''
        Returns the list with headers for given e-mails id-s/uid-s. Accepts
        iterables, string, bytes or single numbers. Fields argument enables
        to retrive only selected fields (for bandwith optimization).
        '''
        headers = list()
        ids_bytes = self._ids_to_bytes(ids)
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
                if isinstance(item, tuple): 
                    # Find message'id
                    if uid:
                        pattern = re.compile(".*UID (?P<id>\d+)")
                    else:
                        pattern = re.compile("(?P<id>\d+)")
                    match = pattern.search(item[0].decode("utf-8"))

                    header = dict(parser.parsestr(item[1].decode("utf-8"), 
                                                  headersonly=True))
                    header["id"] = int(match.group("id")) if match else None
                    headers.append(header)

            return ("OK", headers)
        else:
            return (fetch_status, data)

    def get_emails(self, ids, *, msg_parts = "(RFC822)", uid=False): 
        '''
        Returns the list of emails (email.message.Message) for given id-s/uid-s. 
        Accepts iterables, string, bytes or single numbers.
        '''
        emails = list()
        ids_bytes = self._ids_to_bytes(ids)

        if uid:
            fetch_status, data = self.mail.uid("fetch", ids_bytes, msg_parts)
        else:
            fetch_status, data = self.mail.fetch(ids_bytes, msg_parts)

        if fetch_status == "OK":
            for item in data:
                if item == b')': continue   
                if isinstance(item, tuple):
                    msg = email.message_from_string(item[1].decode())
                    emails.append(msg)

            return ("OK", emails)
        else:
            return (fetch_status, data)


def email_to_dict(msg):
    '''Convert email.message.Message instance to dictionary representation.'''
    output = dict()

    if msg.is_multipart():
        for part in msg.walk():
            pass

    return output


def get_email_header(header_text, default="ascii"):
    """
    Decode header_text.
    source: http://blog.magiksys.net/parsing-email-using-python-header
    """
    try:
        headers = decode_header(header_text)
    except email.Errors.HeaderParseError:
        # This already append in email.base64mime.decode()
        # instead return a sanitized ascii string 
        return header_text.encode('ascii', 'replace').decode('ascii')
    else:
        for i, (text, charset) in enumerate(headers):
            try:
                headers[i] = str(text, charset or default, errors='replace')
            except LookupError:
                headers[i] = str(text, default, errors='replace')
        return "".join(headers)


def get_email_addresses(msg, name):
    """
    Retrieve email address from: From:, To: and Cc
    source: http://blog.magiksys.net/parsing-email-using-python-header
    """
    addrs = email.utils.getaddresses(msg.get_all(name, []))
    for i, (name, addr) in enumerate(addrs):
        if not name and addr:
            # only one string! Is it the address or is it the name ?
            # use the same for both and see later
            name = addr
            
        try:
            # address must be ascii only
            addr = addr.encode('ascii')
        except UnicodeError:
            addr = ''
        else:
            # address must match adress regex
            if not email_address_re.match(addr):
                addr = ''
        addrs[i] = (get_email_header(name), addr)
    return addrs