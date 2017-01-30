import imp
import importlib
import sys
import inspect
import ctypes
import binascii
import socket
from datetime import datetime
import pytz

from app import dtformat_default


def tz2utc(dt, tz, dtformat=dtformat_default):
    '''
    Converts datetime(dt) from given time zone(tz) to utc. If dt is a str,
    parses dt in accordance with dtformat.
    '''
    if isinstance(dt, str):
        dt = datetime.strptime(dt, dtformat)
    dt_utc = tz.localize(dt).astimezone(pytz.utc)
    return dt_utc

def utc2tz(dt, tz, dtformat=dtformat_default):
    '''
    Converts datetime(dt) from utz to given time zone(tz). If dt is a str,
    parses dt in accordance with dtformat.
    '''
    if isinstance(dt, str):
        dt = datetime.strptime(dt, dtformat)
    dt_utz = pytz.utc.localize(dt).astimezone(tz)
    return dt_utz


def merge_dicts(*dict_args):
    '''
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    '''
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def load_module(name, attach = False, force_reload = True):
    '''
    Load module and attach its attributes (attach = True) to global
    namespace.
    '''
    if name in sys.modules and force_reload:
        module = imp.reload(sys.modules[name])
    else:
        module = importlib.import_module(name)
    if attach:
        calling_frame = inspect.stack()[1][0]
        calling_frame.f_locals.update(
            { attr: getattr(module, attr) for attr in dir(module) 
                                          if not attr.startswith("_") }
        )
        ctypes.pythonapi.PyFrame_LocalsToFast(
                ctypes.py_object(calling_frame), ctypes.c_int(0))
    return module


def base64_to_utf16be(s):
    '''Convert base64 encoded data to utf-16be'''
    b = binascii.a2b_base64(s.replace(',', '/') + '===')
    return b.decode("utf-16be")


def utf7_decode(s):
    '''Decode text encoded with utf-7. https://tools.ietf.org/pdf/rfc2152.pdf'''
    r = list()
    decode_chars = list()

    for c in s:
        if c == '&' and not decode_chars:
            decode_chars.append('&')
        elif c == '-' and decode_chars:
            if len(decode_chars) == 1:
                r.append('&')
            else:
                r.append(base64_to_utf16be(''.join(decode_chars[1:])))
                decode_chars = list()
        elif decode_chars:
            decode_chars.append(c)
        else:
            r.append(c)
    if decode_chars:
        r.append(base64_to_utf16be(''.join(decode_chars[1:])))
    bin_str = ''.join(r)
    return bin_str


def utf16be_to_base64(st):
    '''Convert utf16be to base64'''
    st = st.encode("utf-16be")
    return binascii.b2a_base64(st).decode("ascii").rstrip('\n=').replace('/', ',')


def utf7_encode(s):
    '''Encode text decoded with utf-7. https://tools.ietf.org/pdf/rfc2152.pdf'''
    r = list()
    other_chars = list()

    for c in s:
        ordC = ord(c)
        if 0x20 <= ordC <= 0x7e:
            if other_chars:
                r.append('&{0}-'.format(utf16be_to_base64(''.join(other_chars))))
            del other_chars[:]
            r.append(c)
            if c == '&':
                r.append('-')
        else:
            other_chars.append(c)
    if other_chars:
        r.append('&{0}-'.format(utf16be_to_base64(''.join(other_chars))))
        del other_chars[:]
    return str(''.join(r))


def imap_recvall(sock, timeout=5, buflen=1024):
    data_recv = b''
    prev_timeout = sock.gettimeout()
    while True:
        try:
            sock.settimeout(timeout)
            temp_recv = sock.recv(buflen)
        except socket.timeout:
            temp_recv = b""
            break
        if not temp_recv:
            break
        data_recv = data_recv + temp_recv
        if temp_recv.endswith(b"\r\n"):
            break
    sock.settimeout(prev_timeout)
    return data_recv