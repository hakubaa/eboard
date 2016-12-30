import imaplib
import socket
import collections
import re
import email
import datetime
import string
import random

from email.header import decode_header
from email.parser import HeaderParser
from functools import partial#, partialmethod
from app.utils import imap_recvall

# Set proper limit in order to avoid error: 
# 'imaplib.error: command: SELECT => got more than 100000 bytes'
imaplib._MAXLINE = 1000000
socket.setdefaulttimeout(5)

DEFAULT_MAILBOX = "INBOX"


def decode_header_field(msg, name, default="ascii"):
    """
    Decode header_text.
    source: http://blog.magiksys.net/parsing-email-using-python-header
    """
    try:
        headers = decode_header(msg[name])
        headers = list(map(lambda x: x if isinstance(x, tuple) else (x, None), headers))
    except email.errors.HeaderParseError:
        return msg[name].encode('ascii', 'replace').decode('ascii')
    except KeyError:
        return None
    else:
        for i, (text, charset) in enumerate(headers):
            if not isinstance(text, str):
                try:
                    headers[i] = str(text, charset or default, errors='replace')
                except LookupError:
                    headers[i] = str(text, default, errors='replace')
            else:
                headers[i] = text

        return "".join(headers)

def decode_data(data):
    try:
        data = data.decode("ascii")
    except:
        pass
    return data

default_decoders = dict(
    SUBJECT = partial(decode_header_field, name="Subject"),
    FROM    = partial(decode_header_field, name="From"),
    TO      = partial(decode_header_field, name="To"),
    CC      = partial(decode_header_field, name="CC")
)


class ImapClientError(Exception):
    '''Type of exception generated by ImapClient'''
    pass


def imaplib_decorator(args2save = list(), process_data = None):
    def decorator(func):
        def on_call(*args, **kwargs):
            self = args[0]
            for index in args2save:
                self.__dict__[args2save[index]] = args[index]
            try:
                status, data = func(*args, **kwargs)
            except imaplib.IMAP4.error as e:
                raise ImapClientError(str(e)) from None
            except Exception as e:
                raise e

            if process_data:
                data = process_data(data)

            if status != "OK":
                raise ImapClientError(data) 

            return status, data   
        on_call.func = func
        return on_call
    return decorator 


class ImapClient:
    '''
    Wraps imaplib.IMAP4_SSL and provides additional high-level methods for
    accessing messages.
    '''
    def __init__(self, addr, timeout=None):
        socket.setdefaulttimeout(timeout)
        self.mail = imaplib.IMAP4_SSL(addr)
        self.username = None
        self.mailbox = None

    def __getattr__(self, attr):
        '''
        Delagate references to undefined attributes in instance to
        imaplib.IMAP4_SSL.
        '''
        if attr in dir(self.mail):
            return getattr(self.mail, attr)
        raise AttributeError("'%s' object has not attribute '%s'" % 
                             (self.__class__.__name__, attr))

    # login = imaplib_decorator({1: "username"})(imaplib.IMAP4_SSL.login)
    # select = imaplib_decorator({1: "mailbox"})(imaplib.IMAP4_SSL.select)

    def decode_data(data):
        try:
            data = data.decode("ascii")
        except:
            pass
        return data

    create = imaplib_decorator(
                    process_data = decode_data
             )(imaplib.IMAP4_SSL.create)
    delete = imaplib_decorator(
                    process_data = decode_data
             )(imaplib.IMAP4_SSL.delete)
    rename = imaplib_decorator(
                    process_data = decode_data
             )(imaplib.IMAP4_SSL.rename)

    def login(self, username, password):
        '''Identify client using plaintext password.'''
        self.username = username
        try:
            status, msg = self.mail.login(username, password)
        except imaplib.IMAP4.error as e:
            raise ImapClientError(str(e))
        except Exception as e:
            raise e

        if status != "OK":
            raise ImapClientError(msg)
        return status, msg

    def select(self, mailbox=DEFAULT_MAILBOX, readonly=False):
        '''Select mailbox.'''
        self.mailbox = mailbox
        try:
            status, msg = self.mail.select(mailbox, readonly)
        except imaplib.IMAP4.error as e:
            raise ImapClientError(str(e)) from None
        except Exception as e:
            raise e

        if status != "OK":
            raise ImapClientError(msg)
        return status, msg

    def list(self, *args, **kwargs):
        '''
        IMAP LIST: Special-Use Mailboxes: https://tools.ietf.org/html/rfc6154
        Additional attributes: \All \Archive \Drafts \Flagged \Junk \Sent \Trash
        '''
        try:
            status, data = self.mail.list(*args, **kwargs)
        except imaplib.IMAP4.error as e:
            raise ImapClientError(str(e)) from None
        except Exception as e:
            raise e

        if status != "OK":
            raise ImapClientError(data)

        mailboxes = list()
        for mailbox in data:
            metadata, name = re.split(r'"."', mailbox.decode("ascii"))
            name = name.replace("\"", "").replace("'", "").rstrip().lstrip()
            flags = list(map(lambda w: "\\" + w, re.findall("\w+", metadata)))
            mailboxes.append((name, flags))

        return status, mailboxes

    def list_mailbox(self, mailbox=None, *criteria, uid=False, charset=None):
        '''
        Returns the list of e-mails (ids or uids) from selected mailbox. 
        Accepts additional criteria which are passed to search method. 
        '''
        if not mailbox:
            mailbox = self.mailbox
            if not mailbox:
                mailbox = DEFAULT_MAILBOX

        try:
            select_status, msg = self.mail.select(mailbox)
        except imaplib.IMAP4.error as e:
            raise ImapClientError(str(e))
        except Exception as e:
            raise e

        if select_status == "OK":
            if uid:
                search_status, data = self.uid(
                    "search", charset, *criteria or ("ALL",)
                )
            else:
                search_status, data = self.mail.search(
                    charset, *criteria or ("ALL",)
                )
            if search_status == "OK":
                return (search_status, [int(item) for item in data[0].split()])
            else:
                raise ImapClientError(data)
        else:
            raise ImapClientError(msg)

    def csearch(self, criteria, charset="UTF-8", uid=False, 
                timeout=5, clear_socket=True):
        '''
        Returns e-mails (ids or uids) which meet specified criteria from 
        currently selected mailbox. Encodes criteria in accordance
        with charset argument (UTF-8 by default).
        '''
        if not isinstance(criteria, collections.abc.Sequence):
            raise TypeError("expected a sequence object (tuple, list etc.)")

        imap_socket = self.mail.socket()

        # Clear socket
        if clear_socket:
            imap_recvall(imap_socket, timeout=0.00001)

        # Split criteria into required encoding (literals) and not (strings)
        criteria_str = filter(lambda item: not item.get("decode", False), 
                              criteria)
        criteria_lit = list(filter(lambda item: item.get("decode", False), 
                                   criteria)) 

        # Start query in accordance with imap protocol
        tag = random.choice(string.ascii_uppercase) + \
          "".join(str(c) for c in random.sample(range(10), 4))   

        query = tag.encode("ascii")
        if uid:
            query += b" UID"
        query += b" SEARCH "  
        if charset:
            query += b"CHARSET " + charset.encode("ascii") + b" "

        # String criteria are simple and do not require any extra processing
        for crit in criteria_str:
            try:
                query += crit["key"].encode("ascii") + b" " 
                if "value" in crit and crit["value"]:
                    query += crit["value"].encode("ascii") + b" "
            except KeyError:
                raise ImapClientError("invalid criterion")

        # Criteria composed of literals need special treatment
        if criteria_lit:
            try:
                literals = [(criteria_lit[0]["key"], 
                             len(criteria_lit[0]["value"].encode(charset)), 
                             None)]
                for index in range(len(criteria_lit)):
                    if index+1 < len(criteria_lit):
                        key = criteria_lit[index+1]["key"]
                        length = len(criteria_lit[index+1]["value"].encode(charset)) 
                    else:
                        key = None
                        length = None
                    value = criteria_lit[index]["value"]
                    literals.append((key, length, value))
            except KeyError:
                raise ImapClientError("invalid criterion (lack of key or " +
                                      "value, or improper encoding)")

            for key, length, value in literals:
                if value:
                   query += value.encode(charset) + b" " 
                if key and length:
                    query += key.encode("ascii") + b" {" + \
                             str(length).encode("ascii") + b"} "
                query = query[:-1] + b"\r\n"

                imap_socket.send(query)
                data_recv = imap_recvall(imap_socket, timeout=timeout)

                if not data_recv.startswith(b'+'):
                    break  
                query = b""   
        else:
            query = query[:-1] + b"\r\n"
            imap_socket.send(query)
            data_recv = imap_recvall(imap_socket, timeout=timeout)

        resps = data_recv.split(b"\r\n")
        status_raw = None
        data_raw = None
        for resp in resps:
            if re.match(b"^[A-Z0-9]{5}", resp):
                status_raw = resp.decode("ascii")
            if resp.startswith(b"* SEARCH"):
                data_raw = resp.decode("ascii")

        status_match = re.search("^[A-Z0-9]{5} (?P<status>\w*)", status_raw)
        if status_match:
            status = status_match.group("status")
        else:
            status = "ERROR"

        if data_raw:
            data_match = re.search("\* SEARCH (?P<ids>.*)", data_raw) 
            if data_match:
                data = [int(item) for item in data_match.group("ids").split(" ")]
            else:
                data = []
        else:
            data = status_raw
        
        return (status, data)


    def len_mailbox(self, mailbox=None):
        '''Returns number of messages in a mailbox'''
        if not mailbox:
            mailbox = self.mailbox
            if not mailbox:
                mailbox = DEFAULT_MAILBOX

        try:
            select_status, data = self.mail.select(mailbox)
        except imaplib.IMAP4.error as e:
            raise ImapClientError(str(e)) from None
        except Exception as e:
            raise e

        if select_status != "OK":
            raise ImapClientError(data)
        return "OK", int(data[0].decode("utf-8"))

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
        self, ids, *, fields=None, uid=False, 
        header_decoders=default_decoders,
        flags=True,
        sort_by_date=True
    ): 
        '''
        Returns the list with headers for given e-mails id-s/uid-s. Accepts
        iterables, string, bytes or single numbers. Fields argument enables
        to retrive only selected fields (for bandwith optimization).
        '''
        headers = list()
        ids_bytes = self._ids_to_bytes(ids)
        parser = HeaderParser()

        msg_parts = list()
        if flags:
            msg_parts.append("FLAGS")

        if fields:
            msg_parts.append("BODY.PEEK[HEADER.FIELDS (%s)]" % " ".join(fields))
        else:
            msg_parts.append("BODY.PEEK[HEADER]")
        msg_parts = "(" + " ".join(msg_parts) + ")"

        try:
            if uid:
                fetch_status, data = self.mail.uid("fetch", 
                                                   ids_bytes, msg_parts)
            else:
                fetch_status, data = self.mail.fetch(ids_bytes, msg_parts)
        except imaplib.IMAP4.error as e:
            raise ImapClientError(str(e)) from None
        except Exception as e: 
            raise e

        if fetch_status == "OK":
            for item in data:
                if item == b')': continue   
                if isinstance(item, tuple): 
                    header = dict(parser.parsestr(
                        item[1].decode("ascii"), headersonly=True)
                    )

                    # Find message'id
                    if uid:
                        pattern = re.compile(".*UID (?P<id>\d+)")
                    else:
                        pattern = re.compile("(?P<id>\d+)")
                    match_id = pattern.search(item[0].decode("ascii"))
                    header["id"] = int(match_id.group("id")) if match_id else None

                    # Find Flags
                    if flags:
                        pattern = re.compile("FLAGS \((?P<flags>.*)\) ")
                        match_flags = pattern.search(item[0].decode("ascii"))
                        if match_flags:
                            msg_flags = match_flags.group("flags").split(" ")
                            header["Flags"] = [flag for flag in msg_flags
                                               if flag != "" and flag != " "]

                    # Decode select fileds with given decoders
                    for key in header.keys():
                        header[key] = header_decoders.get(
                                    key.upper(), lambda x: x[key])(header)
                    
                    headers.append(header)

            if sort_by_date:
                date_picker = lambda x: datetime.datetime.strptime(
                                            x["Date"], 
                                            "%a, %d %b %Y %H:%M:%S %z"   
                                        )
                headers = sorted(headers, key=date_picker)
            return ("OK", headers)
        else:
            raise ImapClientError(data)

    def get_emails(self, ids, *, msg_parts = "(RFC822)", uid=False): 
        '''
        Returns the list of emails (email.message.Message) for given id-s/uid-s. 
        Accepts iterables, string, bytes or single numbers.
        '''
        emails = list()
        ids_bytes = self._ids_to_bytes(ids)

        try:
            if uid:
                fetch_status, data = self.mail.uid("fetch", ids_bytes, 
                                                   msg_parts)
            else:
                fetch_status, data = self.mail.fetch(ids_bytes, msg_parts)
        except imaplib.IMAP4.error as e:
            raise ImapClientError(str(e)) from None
        except Exception as e:
            raise e

        if fetch_status == "OK":
            for item in data:
                if item == b')': continue   
                if isinstance(item, tuple):
                    msg = email.message_from_string(item[1].decode())
                    emails.append(msg)

            return ("OK", emails)
        else:
            raise ImapClientError(data)

    def move_emails(self, ids, mailbox, *, uid=False):
        '''Move 'message_set' messages onto end of 'new_mailbox'.'''
        ids_bytes = self._ids_to_bytes(ids)

        try:
            if uid:
                copy_status, data = self.mail.uid("copy", ids_bytes, mailbox)
            else:
                copy_status, data = self.mail.copy(ids_bytes, mailbox)
        except imaplib.IMAP4.error as e:
            raise ImapClientError(str(e)) from None
        except Exception as e:
            raise e
        
        if copy_status != "OK":
            if data[0]:
                data = data[0].decode("ascii")
            raise ImapClientError(data)

        return copy_status, data

    def store(self, ids, flags, *, command, uid=False):
        '''Alters flag dispositions for messages in mailbox.'''
        ids_bytes = self._ids_to_bytes(ids)

        if isinstance(flags, str):
            flags_str = flags
        elif isinstance(flags, collections.Iterable):
            flags_str = " ".join(flags)
        else:
            flags_str = flags

        try: 
            if uid:
                store_status, data = self.mail.uid("store", ids_bytes, command, 
                                                   flags_str)
            else:   
                store_status, data = self.mail.store(ids_bytes, command, 
                                                     flags_str)
        except imaplib.IMAP4.error as e:
            raise ImapClientError(str(e)) from None
        except Exception as e:
            raise e

        data = data[0].decode()

        if store_status != "OK":
            raise ImapClientError(data)

        return store_status, data

    def add_flags(self, ids, flags, *, uid=False): 
        return self.store(ids, flags, command="+FLAGS", uid=uid)

    def set_flags(self, ids, flags, *, uid=False): 
        return self.store(ids, flags, command="FLAGS", uid=uid)

    def remove_flags(self, ids, flags, *, uid=False): 
        return self.store(ids, flags, command="-FLAGS", uid=uid)


def email_to_dict(msg, header_decoders = default_decoders):
    '''Convert email.message.Message instance to dictionary representation.'''
    output = dict(header={})

    for key in msg.keys():
        output["header"][key] = header_decoders.get(
                                    key.upper(), lambda x: x[key])(msg)

    if msg.is_multipart():
        output["body"] = list()
        for part in msg.get_payload():
            output["body"].append(email_to_dict(part))
    else:
        content = msg.get_payload(decode=True)
        output["body"] = decode_content(content, msg.get_charset())

    return output


def decode_content(content, charset=None):
    if charset:
        content = content.decode(charset)
    else:
        # Try one of the default charset
        for chset in ['ascii', 'utf-8', 'utf-16', 'windows-1252', 'cp850']:
            try: 
                content = content.decode(chset)
                break
            except UnicodeError:
                pass
    return content


content_prefs = dict(
    text=dict(
        plain=0,
        html=1
    ),
    multipart=dict(
        alternative=2,
        mixed=3
    )
)

def get_msg_pref(msg):
    content_type = content_prefs.get(msg.get_content_maintype(), None)
    if content_type:
        content_subtype = content_type.get(msg.get_content_subtype(), -1)
        return content_subtype
    else:
        return -1

def process_email_for_display(msg, header_decoders = default_decoders):
    '''
    Convert email.message.Message instance to dictionary representation.
    email: {
        header: [],
        type: node/plan/attachment/unsupported
        content: [
            { header: [], type: "content": content: "bla bla" },
            ...
        ]
    }
    '''
    output = dict(header=dict())

    for key in msg.keys():
        output["header"][key] = header_decoders.get(
                                    key.upper(), lambda x: x[key])(msg)
    if msg.is_multipart():
        output["type"] = "node"

        msg_subtype = msg.get_content_subtype()
        if msg_subtype == "alternative":
            msg_parts = msg.get_payload()
            pref_part = msg_parts[0]
            for part in msg_parts[1:]:
                if get_msg_pref(part) > get_msg_pref(pref_part):
                    pref_part = part
            output["content"] = [process_email_for_display(pref_part, 
                                                           header_decoders)]
        elif msg_subtype == "mixed":
            output["content"] = [
                process_email_for_display(part, header_decoders) 
                    for part in msg.get_payload() 
            ]
        else:
            output["type"] = "unsupported"
            output["content"] = None
    else:
        output["type"] = "plain"

        msg_maintype = msg.get_content_maintype()
        if msg_maintype == "text":
            if "attachment" in msg.get("Content-Disposition", ""):
                output["type"] = "attachment" # override content type
                output["content"] = None
            else:
                content = msg.get_payload(decode=True)
                body = decode_content(content, msg.get_charset())
                output["content"] = body
        else:
            output["type"] = "unsupported"
            output["content"] = None

    return output