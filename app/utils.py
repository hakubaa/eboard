import imp
import importlib
import sys
import inspect
import ctypes
import binascii

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

