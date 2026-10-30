"""Window-scoped IMM input for the existing GPU field, using public Win32 APIs.

Only the focused Blender window on this process's UI thread is subclassed.
Callbacks queue text, never access bpy, and are pinned until Windows releases
them. No global hook, keymap edit, clipboard composition or private Blender ABI.
"""
import ctypes as C
from contextlib import contextmanager
import sys

from .session import Composition


WM_NCDESTROY = 0x0082
WM_KILLFOCUS = 0x0008
WM_INPUT = 0x00FF
WM_CHAR = 0x0102
WM_UNICHAR = 0x0109
WM_IME_STARTCOMPOSITION = 0x010D
WM_IME_ENDCOMPOSITION = 0x010E
WM_IME_COMPOSITION = 0x010F
WM_IME_SETCONTEXT = 0x0281
WM_IME_NOTIFY = 0x0282
WM_IME_CHAR = 0x0286
GCS_COMPSTR = 0x0008
GCS_RESULTSTR = 0x0800
ISC_SHOWUICOMPOSITIONWINDOW = 0x80000000
MODIFIERS = {0x10, 0x11, 0x12, 0x5B, 0x5C, *range(0xA0, 0xA6)}
NAVIGATION = {0x08, 0x09, 0x0D, 0x1B, *range(0x21, 0x29), 0x2D, 0x2E}
COMMANDS = {0x08: "BACK_SPACE", 0x0D: "RET", 0x1B: "ESC", 0x26: "UP_ARROW",
            0x28: "DOWN_ARROW", 0x2E: "DEL"}

# Keep native callbacks pinned even when a hot update removes the old package
# from sys.modules. Only detached/destroyed-window callbacks may be released.
_LIVE_SESSIONS = getattr(sys, "_node_console_ime_receivers", {})
sys._node_console_ime_receivers = _LIVE_SESSIONS
UINT, LONG, WORD = C.c_uint32, C.c_int32, C.c_uint16
HANDLE, WPARAM, LPARAM = C.c_void_p, C.c_size_t, C.c_ssize_t


class POINT(C.Structure):
    _fields_ = [("x", LONG), ("y", LONG)]


class RECT(C.Structure):
    _fields_ = [(name, LONG) for name in ("left", "top", "right", "bottom")]


class CANDIDATEFORM(C.Structure):
    _fields_ = [("index", UINT), ("style", UINT), ("pos", POINT), ("area", RECT)]


class COMPOSITIONFORM(C.Structure):
    _fields_ = [("style", UINT), ("pos", POINT), ("area", RECT)]


class RAWINPUTHEADER(C.Structure):
    _fields_ = [("type", UINT), ("size", UINT), ("device", HANDLE), ("wparam", WPARAM)]


class RAWKEYBOARD(C.Structure):
    _fields_ = [(name, WORD) for name in ("scan", "flags", "reserved", "key")]
    _fields_ += [("message", UINT), ("extra", UINT)]


class GUITHREADINFO(C.Structure):
    _fields_ = [("size", UINT), ("flags", UINT)]
    _fields_ += [(name, HANDLE) for name in ("active", "focus", "capture", "menu", "move", "caret")]
    _fields_ += [("caret_rect", RECT)]


class WinAPI:
    """Explicit pointer-width signatures; Windows libraries are loaded lazily."""
    def __init__(self):
        if sys.platform != "win32":
            raise RuntimeError("Windows IME requires Windows")
        self.callback_type = C.WINFUNCTYPE(LPARAM, HANDLE, UINT, WPARAM, LPARAM, WPARAM, WPARAM)
        user = C.WinDLL("user32.dll", use_last_error=True, winmode=0x800)
        imm = C.WinDLL("imm32.dll", use_last_error=True, winmode=0x800)
        common = C.WinDLL("comctl32.dll", use_last_error=True, winmode=0x800)
        kernel = C.WinDLL("kernel32.dll", use_last_error=True, winmode=0x800)

        def bind(dll, name, result, *args):
            function = getattr(dll, name)
            function.restype, function.argtypes = result, list(args)
            setattr(self, name, function)

        for name in ("GetFocus", "GetForegroundWindow"):
            bind(user, name, HANDLE)
        bind(user, "IsWindow", LONG, HANDLE)
        bind(user, "GetWindowThreadProcessId", UINT, HANDLE, C.POINTER(UINT))
        bind(user, "GetClassNameW", LONG, HANDLE, C.c_wchar_p, LONG)
        bind(user, "GetClientRect", LONG, HANDLE, C.POINTER(RECT))
        bind(user, "GetKeyState", C.c_int16, LONG)
        bind(user, "MapVirtualKeyW", UINT, UINT, UINT)
        bind(user, "GetRawInputData", UINT, HANDLE, UINT, HANDLE, C.POINTER(UINT), UINT)
        bind(user, "GetGUIThreadInfo", LONG, UINT, C.POINTER(GUITHREADINFO))
        bind(user, "CreateCaret", LONG, HANDLE, HANDLE, LONG, LONG)
        bind(user, "SetCaretPos", LONG, LONG, LONG)
        bind(user, "DestroyCaret", LONG)
        bind(user, "DefWindowProcW", LPARAM, HANDLE, UINT, WPARAM, LPARAM)
        bind(common, "DefSubclassProc", LPARAM, HANDLE, UINT, WPARAM, LPARAM)
        bind(common, "SetWindowSubclass", LONG, HANDLE, self.callback_type, WPARAM, WPARAM)
        bind(common, "RemoveWindowSubclass", LONG, HANDLE, self.callback_type, WPARAM)
        bind(kernel, "GetCurrentProcessId", UINT)
        bind(kernel, "GetCurrentThreadId", UINT)
        bind(imm, "ImmGetContext", HANDLE, HANDLE)
        bind(imm, "ImmReleaseContext", LONG, HANDLE, HANDLE)
        bind(imm, "ImmAssociateContext", HANDLE, HANDLE, HANDLE)
        bind(imm, "ImmAssociateContextEx", LONG, HANDLE, HANDLE, UINT)
        bind(imm, "ImmNotifyIME", LONG, HANDLE, UINT, UINT, UINT)
        bind(imm, "ImmGetCompositionStringW", LONG, HANDLE, UINT, HANDLE, UINT)
        bind(imm, "ImmSetCandidateWindow", LONG, HANDLE, C.POINTER(CANDIDATEFORM))
        bind(imm, "ImmSetCompositionWindow", LONG, HANDLE, C.POINTER(COMPOSITIONFORM))

    def owner_window(self):
        hwnd = self.GetFocus()
        pid = UINT()
        thread = self.GetWindowThreadProcessId(hwnd, C.byref(pid)) if hwnd else 0
        name = C.create_unicode_buffer(256)
        if hwnd:
            self.GetClassNameW(hwnd, name, len(name))
        if (not hwnd or thread != self.GetCurrentThreadId() or pid.value != self.GetCurrentProcessId()
                or self.GetForegroundWindow() != hwnd or name.value != "GHOST_WindowClass"):
            raise RuntimeError("No focused Blender window on the current UI thread")
        return hwnd

    def context(self, hwnd):
        value = self.ImmGetContext(hwnd)
        if value:
            self.ImmReleaseContext(hwnd, value)
        return value

    @contextmanager
    def acquire(self, hwnd, expected):
        context = self.ImmGetContext(hwnd)
        try:
            if not context or context != expected:
                raise RuntimeError("The input context changed ownership")
            yield context
        finally:
            if context:
                self.ImmReleaseContext(hwnd, context)

    def composition(self, hwnd, expected, flags):
        # Keep the acquired context alive while reading both result and preedit.
        with self.acquire(hwnd, expected) as context:
            return {kind: self.text(context, kind) for kind in (GCS_RESULTSTR, GCS_COMPSTR) if flags & kind}

    def text(self, context, kind):
        size = self.ImmGetCompositionStringW(context, kind, None, 0)
        if size < 0 or size > 1024 * 1024 or size % 2:
            raise RuntimeError("Invalid IME composition buffer")
        if not size:
            return ""
        buffer = C.create_string_buffer(size)
        actual = self.ImmGetCompositionStringW(context, kind, buffer, size)
        if actual < 0 or actual > size or actual % 2:
            raise RuntimeError("Invalid IME composition read")
        return buffer.raw[:actual].decode("utf-16-le")

    def raw_key(self, handle):
        size = UINT()
        header_size = C.sizeof(RAWINPUTHEADER)
        if self.GetRawInputData(handle, 0x10000003, None, C.byref(size), header_size) == 0xFFFFFFFF:
            raise RuntimeError("Cannot inspect raw input")
        if size.value < header_size or size.value > 1024 * 1024:
            raise RuntimeError("Invalid raw input buffer")
        buffer = C.create_string_buffer(size.value)
        actual = self.GetRawInputData(handle, 0x10000003, buffer, C.byref(size), header_size)
        if actual == 0xFFFFFFFF or actual < header_size:
            raise RuntimeError("Cannot read raw input")
        if RAWINPUTHEADER.from_buffer(buffer).type != 1:
            return None
        if actual < header_size + C.sizeof(RAWKEYBOARD):
            raise RuntimeError("Invalid raw keyboard buffer")
        key = RAWKEYBOARD.from_buffer(buffer, header_size)
        return key.key, bool(key.flags & 1)

    def shortcut_held(self):
        down = lambda key: bool(self.GetKeyState(key) & 0x8000)
        # AltGr is text input, not Ctrl+Alt command input.
        return down(0x5B) or down(0x5C) or ((down(0x11) or down(0x12)) and not down(0xA5))

    def printable(self, key):
        return key not in NAVIGATION and bool(self.MapVirtualKeyW(key, 2))

    def make_caret(self, hwnd):
        info = GUITHREADINFO()
        info.size = C.sizeof(info)
        # Never replace a native text field's existing system caret.
        return bool(self.GetGUIThreadInfo(0, C.byref(info)) and not info.caret
                    and self.CreateCaret(hwnd, None, 1, 1))

    def move_caret(self, hwnd, context, rect, own_caret):
        client = RECT()
        if not self.GetClientRect(hwnd, C.byref(client)):
            return
        x, bottom, width, height = rect
        # Blender's POST_PIXEL coordinates and this DPI-aware client rect are
        # physical client pixels, with opposite Y directions. Do not rescale DPI.
        x = max(0, min(client.right, round(x)))
        y = max(0, min(client.bottom, round(client.bottom - bottom - height)))
        area = RECT(x, y, x + max(1, round(width)), y + max(1, round(height)))
        candidate = CANDIDATEFORM(0, 0x80, POINT(x, area.bottom), area)  # CFS_EXCLUDE
        composition = COMPOSITIONFORM(0x2, POINT(x, y), area)  # CFS_POINT
        with self.acquire(hwnd, context) as acquired:
            self.ImmSetCandidateWindow(acquired, C.byref(candidate))
            self.ImmSetCompositionWindow(acquired, C.byref(composition))
        if own_caret:
            self.SetCaretPos(x, y)


class WindowsSession(Composition):
    def __init__(self, api=None):
        super().__init__()
        self.api = api or WinAPI()
        self.hwnd = self.api.owner_window()
        if any(item.hwnd == self.hwnd and not item.closed for item in _LIVE_SESSIONS.values()):
            raise RuntimeError("A native search already owns this window")
        self.token = id(self)
        self.context = self.previous = None
        self.attached = self.own_caret = self.associated = False
        self.composing = self.failed = False
        self.held = set()
        self.held_commands = {}
        self.high_surrogate = None
        self.caret_rect = None
        self.callback = self.api.callback_type(self._callback)
        try:
            self.previous = self.api.context(self.hwnd)
            if not self.api.SetWindowSubclass(self.hwnd, self.callback, self.token, 0):
                raise RuntimeError("Could not attach Windows input receiver")
            self.attached = True
            _LIVE_SESSIONS[self.token] = self
            if not self.previous:
                # Borrow the system's default context to retain the user's IME
                # language/conversion mode. Never force open status or destroy it.
                if not self.api.ImmAssociateContextEx(self.hwnd, None, 0x10):
                    raise RuntimeError("Could not enable the system IME context")
                self.associated = True
            self.context = self.api.context(self.hwnd)
            if not self.context:
                raise RuntimeError("No system IME input context")
            self.own_caret = self.api.make_caret(self.hwnd)
        except Exception:
            self.close()
            raise

    def _callback(self, hwnd, message, wparam, lparam, _token, _data):
        try:
            if message == WM_NCDESTROY:
                self.close()
                _LIVE_SESSIONS.pop(self.token, None)
            elif not self.closed and not self.failed:
                result = self._message(message, wparam, lparam)
                if result is not None:
                    return result
        except Exception:
            # ctypes callbacks must never unwind into user32. Stop processing
            # text and let the modal timer close the search without logging input.
            self.failed = True
            return self.api.DefWindowProcW(hwnd, message, wparam, lparam)
        return self.api.DefSubclassProc(hwnd, message, wparam, lparam)

    def _message(self, message, wparam, lparam):
        if message == WM_KILLFOCUS:
            self.close()
            return None
        if message == WM_IME_SETCONTEXT:
            return self.api.DefWindowProcW(self.hwnd, message, wparam,
                                          lparam & ~ISC_SHOWUICOMPOSITIONWINDOW)
        if message == WM_IME_STARTCOMPOSITION:
            self.composing = True
            self.high_surrogate = None
            return 0
        if message == WM_IME_COMPOSITION:
            strings = self.api.composition(self.hwnd, self.context, lparam)
            if lparam & GCS_RESULTSTR:
                self._committed_text(strings[GCS_RESULTSTR])
            if lparam & GCS_COMPSTR:
                text = strings[GCS_COMPSTR]
                self.composing = bool(text)
                self.receive(2, text)
            elif not lparam:
                self.receive(2, "")
                self.composing = False
            return 0
        if message == WM_IME_ENDCOMPOSITION:
            self.composing = False
            self.receive(2, "")
            return 0
        if message == WM_IME_NOTIFY:
            if wparam in {3, 5} and self.caret_rect:  # candidate changed/opened
                self.api.move_caret(self.hwnd, self.context, self.caret_rect, self.own_caret)
            return self.api.DefWindowProcW(self.hwnd, message, wparam, lparam)
        if message == WM_IME_CHAR:
            return 0  # Result already consumed; do not create duplicate WM_CHAR.
        if message == WM_INPUT:
            key = self.api.raw_key(lparam)
            if key and self._block_raw(*key):
                # Required cleanup for foreground raw-input packets, bypassing
                # Blender's independent ToUnicode/raw-key dispatch only here.
                return self.api.DefWindowProcW(self.hwnd, message, wparam, lparam)
        if message in {WM_CHAR, WM_UNICHAR}:
            if message == WM_UNICHAR and wparam == 0xFFFF:
                return 1
            if not self.composing and not self.api.shortcut_held():
                self._character(wparam)
            return 0
        return None

    def _block_raw(self, key, released):
        if key in MODIFIERS:
            return False
        if key in self.held:
            if released:
                self.held.remove(key)
                self.held_commands.pop(key, None)
            elif not self.composing and key in COMMANDS and self.held_commands.get(key):
                self.receive(5, (COMMANDS[key], False))
            return True
        shortcut = self.api.shortcut_held()
        command = COMMANDS.get(key) if not shortcut else None
        paste = (key == 0x56 and shortcut and self.api.GetKeyState(0x11) & 0x8000
                 and not any(self.api.GetKeyState(k) & 0x8000 for k in (0x12, 0x5B, 0x5C))
                 and not self.composing)
        if not released and not self.composing and (command or paste):
            self.receive(5, (command or "V", bool(paste)))
        block = self.composing or bool(command) or bool(paste) or (not shortcut and self.api.printable(key))
        if block and not released:
            self.held.add(key)
            self.held_commands[key] = bool(command and not self.composing)
        return block

    def _character(self, code):
        if 0xD800 <= code <= 0xDBFF:
            self.high_surrogate = code
            return
        high, self.high_surrogate = self.high_surrogate, None
        if 0xDC00 <= code <= 0xDFFF:
            if high is None:
                return
            code = 0x10000 + ((high - 0xD800) << 10) + code - 0xDC00
        if not 0x20 <= code <= 0x10FFFF or code == 0x7F:
            return
        self._committed_text(chr(code))

    def _committed_text(self, text):
        if text in {"`", "·"}:
            self.receive(2, "")
            self.receive(5, ("ACCENT_GRAVE", False))
        else:
            self.receive(1, text)

    def drain_actions(self, query, command):
        # Preserve ordering when Windows delivers text, backspace and Enter in
        # one event-pump batch, before Blender runs its Python modal callbacks.
        while self.events and not self.closed:
            kind, text = self.events.popleft()
            if kind == 1:
                self.preedit = ""
                query += text
            elif kind == 2:
                self.preedit = text
            elif kind == 5:
                query = command(query, *text)
        return query

    def sync(self, query):
        # IMM only owns the in-progress composition; committed text stays in the
        # existing modal query, including backspace, paste and clear operations.
        pass

    def focused(self):
        return (not self.closed and not self.failed and self.api.GetFocus() == self.hwnd
                and self.api.GetForegroundWindow() == self.hwnd
                and self.api.context(self.hwnd) == self.context)

    def reacquire(self):
        return self.focused()  # Never steal focus or override another field's context.

    def caret(self, x, y, width, height):
        if self.focused():
            self.caret_rect = (x, y, width, height)
            self.api.move_caret(self.hwnd, self.context, self.caret_rect, self.own_caret)

    def close(self):
        if self.closed:
            return
        super().close()
        self.held.clear()
        self.held_commands.clear()
        self.high_surrogate = None
        valid = self.api.IsWindow(self.hwnd)
        if valid and self.context and self.api.context(self.hwnd) == self.context:
            if self.composing:
                self.api.ImmNotifyIME(self.context, 0x15, 0x4, 0)  # CPS_CANCEL, not commit
            if self.associated:
                self.api.ImmAssociateContext(self.hwnd, self.previous)
        if self.own_caret:
            self.api.DestroyCaret()
            self.own_caret = False
        if self.attached and valid:
            if not self.api.RemoveWindowSubclass(self.hwnd, self.callback, self.token):
                return  # Keep callback pinned and inert until WM_NCDESTROY.
        self.attached = False
        _LIVE_SESSIONS.pop(self.token, None)
