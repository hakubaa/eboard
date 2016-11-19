import imp
import importlib
import sys
import inspect
import ctypes


def load_module(name, attach = False, force_reload = True):
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
