"""Composition state and the package-local macOS text input receiver."""
from collections import deque
import ctypes
import sys


class Composition:
    def __init__(self):
        self.preedit = ""
        self.events = deque()
        self.diagnostics = deque(maxlen=100)
        self.closed = False

    def receive(self, kind, text):
        if not self.closed:
            if kind == 3:
                self.diagnostics.append(text)
            else:
                self.events.append((kind, text))

    def drain(self, query):
        while self.events:
            kind, text = self.events.popleft()
            if kind == 1:
                self.preedit = ""
                query += text
            elif kind == 2:
                self.preedit = text
            elif kind == 4:
                self.preedit = ""
                query = text
        return query

    def close(self):
        self.closed = True
        self.events.clear()
        self.diagnostics.clear()
        self.preedit = ""


class CocoaSession(Composition):
    CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p)

    def __init__(self, library):
        super().__init__()
        if sys.platform != "darwin":
            raise RuntimeError("The Cocoa text input backend requires macOS.")
        self.lib = ctypes.CDLL(str(library))
        self.lib.nc_ime_start.argtypes = [self.CALLBACK]
        self.lib.nc_ime_start.restype = ctypes.c_int
        self.lib.nc_ime_caret.argtypes = [ctypes.c_double] * 4
        self.lib.nc_ime_caret.restype = None
        self.lib.nc_ime_focused.argtypes = []
        self.lib.nc_ime_focused.restype = ctypes.c_int
        self.lib.nc_ime_reacquire.argtypes = []
        self.lib.nc_ime_reacquire.restype = ctypes.c_int
        self.lib.nc_ime_sync.argtypes = [ctypes.c_char_p]
        self.lib.nc_ime_sync.restype = None
        self.lib.nc_ime_input_source.argtypes = []
        self.lib.nc_ime_input_source.restype = ctypes.c_char_p
        self.lib.nc_ime_stop.argtypes = []
        self.lib.nc_ime_stop.restype = None
        self.callback = self.CALLBACK(
            lambda kind, text: self.receive(kind, (text or b"").decode("utf-8")))
        if not self.lib.nc_ime_start(self.callback):
            self.closed = True
            raise RuntimeError("Could not acquire input focus: " + "; ".join(self.diagnostics))

    def close(self):
        if self.closed:
            return
        super().close()
        self.lib.nc_ime_stop()

    def focused(self):
        return not self.closed and bool(self.lib.nc_ime_focused())

    def reacquire(self):
        return not self.closed and bool(self.lib.nc_ime_reacquire())

    def sync(self, query):
        if not self.closed:
            self.lib.nc_ime_sync(query.encode("utf-8"))

    def caret(self, x, y, width, height):
        if not self.closed:
            self.lib.nc_ime_caret(x, y, width, height)

    def input_source(self):
        return (self.lib.nc_ime_input_source() or b"").decode("utf-8")
