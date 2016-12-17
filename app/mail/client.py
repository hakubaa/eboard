import imaplib
import socket
import collections
import re
import email
from email.header import decode_header
from email.parser import HeaderParser
from functools import partial, partialmethod

# Set proper limit in order to avoid error: 
# 'imaplib.error: command: SELECT => got more than 100000 bytes'
imaplib._MAXLINE = 1000000


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

default_decoders = dict(
    SUBJECT = partial(decode_header_field, name="Subject"),
    FROM    = partial(decode_header_field, name="From"),
    TO      = partial(decode_header_field, name="To"),
    CC      = partial(decode_header_field, name="CC")
)


class ImapClientError(Exception):
    '''Type of exception generated by ImapClient'''
    pass


def imaplib_decorator(args2save = None):
    def decorator(func):
        def on_call(*args, **kwargs):
            self = args[0]
            for index in args2save:
                self.__dict__[args2save[index]] = args[index]
            try:
                status, msg = func(*args, **kwargs)
            except imaplib.IMAP4.error as e:
                raise ImapClientError(str(e)) from None
            except:
                raise e

            if status == "ERROR":
                raise ImapClientError(msg) 
            return status, msg   
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

    def login(self, username, password):
        '''Identify client using plaintext password.'''
        self.username = username
        try:
            status, msg = self.mail.login(username, password)
        except imaplib.IMAP4.error as e:
            raise ImapClientError(str(e))
        except:
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
        except:
            raise e

        if status != "OK":
            raise ImapClientError(msg)
        return status, msg

    def list(self, *args, **kwargs):
        try:
            status, msg = self.mail.list(*args, **kwargs)
        except imaplib.IMAP4.error as e:
            raise ImapClientError(str(e)) from None
        except:
            raise e

        if status != "OK":
            raise ImapClientError(msg)
        return status, msg

    def list_mailbox(self, mailbox=None, *criteria, uid=False):
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
        except: 
            raise e

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
                raise ImapClientError(data)
        else:
            raise ImapClientError(msg)

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
        except:
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
        flags=True
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
        except:
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
        except e:
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
        except:
            raise e

        data = data[0].decode("ascii")

        if copy_status != "OK":
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
        except:
            raise e

        data = data[0].decode()

        if store_status != "OK":
            raise ImapClientError(data)

        return store_status, data

    add_flags = partialmethod(store, command="+FLAGS")
    set_flags = partialmethod(store, command="FLAGS")
    remove_flags = partialmethod(store, command="-FLAGS")



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
