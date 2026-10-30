"""Win32 contract tests with fake OS calls, not proof of real IME behavior."""
import ctypes as C
import unittest
from unittest.mock import Mock, patch

from ime_input import windows as w


class FakeAPI:
    def __init__(self, previous=None):
        self.hwnd = 0x123400000
        self.current = previous
        self.owner_window = Mock(return_value=self.hwnd)
        self.GetFocus = Mock(return_value=self.hwnd)
        self.GetForegroundWindow = Mock(return_value=self.hwnd)
        self.context = Mock(side_effect=lambda hwnd: self.current)
        self.IsWindow = Mock(return_value=True)
        self.callback_type = lambda callback: callback
        self.SetWindowSubclass = Mock(return_value=1)
        self.RemoveWindowSubclass = Mock(return_value=1)
        self.ImmAssociateContextEx = Mock(side_effect=self.enable)
        self.ImmAssociateContext = Mock(side_effect=self.restore)
        self.ImmNotifyIME = Mock()
        self.DestroyCaret = Mock()
        self.make_caret = Mock(return_value=True)
        self.move_caret = Mock()
        self.DefWindowProcW = Mock(return_value=10)
        self.DefSubclassProc = Mock(return_value=20)
        self.shortcut_held = Mock(return_value=False)
        self.GetKeyState = Mock(return_value=0)
        self.printable = Mock(side_effect=lambda key: 0x30 <= key <= 0x5A or key in {0x20, 0xC0})
        self.raw_key = Mock()
        self.strings = {}
        self.text = Mock(side_effect=lambda context, kind: self.strings.get(kind, ""))
        self.composition = lambda hwnd, context, flags: {
            kind: self.text(context, kind) for kind in (w.GCS_RESULTSTR, w.GCS_COMPSTR) if flags & kind}

    def enable(self, hwnd, context, flags):
        self.current = 0x234500000
        return 1

    def restore(self, hwnd, context):
        self.current = context


class WindowsSessionTests(unittest.TestCase):
    def open(self, previous=None):
        api = FakeAPI(previous)
        session = w.WindowsSession(api)
        self.addCleanup(session.close)
        return session, api

    def message(self, session, message, wp=0, lp=0):
        return session.callback(session.hwnd, message, wp, lp, session.token, 0)

    def raw(self, session, api, key, released=False):
        api.raw_key.return_value = key, released
        return self.message(session, w.WM_INPUT)

    def test_association_restored_and_callback_unpinned_on_close(self):
        session, api = self.open()
        self.assertIn(session.token, w._LIVE_SESSIONS)
        self.assertTrue(session.reacquire())
        session.close()
        session.close()
        api.ImmAssociateContext.assert_called_once_with(session.hwnd, None)
        api.RemoveWindowSubclass.assert_called_once()
        api.DestroyCaret.assert_called_once()
        self.assertNotIn(session.token, w._LIVE_SESSIONS)

    def test_existing_context_not_replaced_or_destroyed(self):
        session, api = self.open(previous=9876)
        session.close()
        api.ImmAssociateContextEx.assert_not_called()
        api.ImmAssociateContext.assert_not_called()

    def test_other_owner_context_is_not_overwritten_on_close(self):
        session, api = self.open()
        api.current = 112233
        self.assertFalse(session.reacquire())
        session.close()
        api.ImmAssociateContext.assert_not_called()

    def test_focus_loss_does_not_reacquire_or_steal_focus(self):
        session, api = self.open()
        api.GetFocus.return_value = 112233
        self.assertFalse(session.reacquire())
        self.message(session, w.WM_KILLFOCUS)
        self.assertTrue(session.closed)

    def test_reopen_does_not_leave_a_second_receiver(self):
        first, api = self.open()
        with self.assertRaises(RuntimeError):
            w.WindowsSession(api)
        first.close()
        second = w.WindowsSession(api)
        self.addCleanup(second.close)
        first.close()
        self.assertTrue(second.reacquire())

    def test_attach_failure_leaves_input_context_alone(self):
        api = FakeAPI()
        api.SetWindowSubclass.return_value = 0
        with self.assertRaises(RuntimeError):
            w.WindowsSession(api)
        api.ImmAssociateContextEx.assert_not_called()
        api.RemoveWindowSubclass.assert_not_called()

    def test_enable_failure_unhooks(self):
        api = FakeAPI()
        api.ImmAssociateContextEx.side_effect = None
        api.ImmAssociateContextEx.return_value = 0
        with self.assertRaises(RuntimeError):
            w.WindowsSession(api)
        api.RemoveWindowSubclass.assert_called_once()

    def test_failed_unhook_keeps_callback_pinned_and_inert(self):
        session, api = self.open()
        api.RemoveWindowSubclass.return_value = 0
        session.close()
        self.assertIs(w._LIVE_SESSIONS[session.token], session)
        self.message(session, w.WM_CHAR, ord("a"))
        self.assertFalse(session.events)
        self.message(session, w.WM_NCDESTROY)
        self.assertNotIn(session.token, w._LIVE_SESSIONS)

    def test_first_letter_and_repeat_do_not_leak_through_raw_input(self):
        session, api = self.open()
        for released in (False, False, True):
            self.assertEqual(self.raw(session, api, 0x4A, released), 10)
        self.assertFalse(session.events)
        api.DefSubclassProc.assert_not_called()

    def test_english_text_comes_once_from_wm_char(self):
        session, api = self.open()
        self.raw(session, api, 0x4A)
        self.message(session, w.WM_CHAR, ord("j"))
        self.raw(session, api, 0x4A, True)
        self.assertEqual(session.drain(""), "j")

    def test_modifiers_and_shortcuts_still_reach_blender(self):
        session, api = self.open()
        api.shortcut_held.return_value = True
        for key in (0x10, 0x11, 0x12, 0x5B, 0x47, 0x54):
            self.assertEqual(self.raw(session, api, key), 20)
        self.assertFalse(session.events)

    def test_non_keyboard_raw_devices_are_untouched(self):
        session, api = self.open()
        api.raw_key.return_value = None
        self.assertEqual(self.message(session, w.WM_INPUT), 20)

    def test_composition_and_commit_not_duplicated(self):
        session, api = self.open()
        self.message(session, w.WM_IME_STARTCOMPOSITION)
        api.strings[w.GCS_COMPSTR] = "ji he"
        self.message(session, w.WM_IME_COMPOSITION, lp=w.GCS_COMPSTR)
        self.assertEqual(session.drain("before"), "before")
        self.assertEqual(session.preedit, "ji he")
        api.strings[w.GCS_RESULTSTR] = "集合"
        self.message(session, w.WM_IME_COMPOSITION, lp=w.GCS_RESULTSTR)
        self.message(session, w.WM_IME_CHAR, ord("集"))
        self.message(session, w.WM_IME_ENDCOMPOSITION)
        self.assertEqual(session.drain("before"), "before集合")
        self.assertEqual(session.preedit, "")

    def test_composition_commit_followed_by_new_preedit(self):
        session, api = self.open()
        api.strings.update({w.GCS_RESULTSTR: "集合", w.GCS_COMPSTR: "xin"})
        self.message(session, w.WM_IME_COMPOSITION, lp=w.GCS_RESULTSTR | w.GCS_COMPSTR)
        self.assertEqual(session.drain(""), "集合")
        self.assertEqual(session.preedit, "xin")

    def test_candidate_enter_repeat_and_release_cannot_create_node(self):
        session, api = self.open()
        self.message(session, w.WM_IME_STARTCOMPOSITION)
        self.raw(session, api, 0x0D)
        api.strings[w.GCS_RESULTSTR] = "集合"
        self.message(session, w.WM_IME_COMPOSITION, lp=w.GCS_RESULTSTR)
        self.message(session, w.WM_IME_ENDCOMPOSITION)
        self.raw(session, api, 0x0D)  # held/repeated confirmation is still swallowed
        self.raw(session, api, 0x0D, True)
        command = Mock()
        self.assertEqual(session.drain_actions("", command), "集合")
        command.assert_not_called()
        self.raw(session, api, 0x0D)  # next deliberate Enter creates
        command.return_value = "集合"
        session.drain_actions("集合", command)
        command.assert_called_once_with("集合", "RET", False)

    def test_escape_cancels_composition_only(self):
        session, api = self.open()
        self.message(session, w.WM_IME_STARTCOMPOSITION)
        self.raw(session, api, 0x1B)
        self.message(session, w.WM_IME_COMPOSITION)
        self.message(session, w.WM_IME_ENDCOMPOSITION)
        self.raw(session, api, 0x1B, True)
        command = Mock()
        self.assertEqual(session.drain_actions("集合", command), "集合")
        command.assert_not_called()
        self.assertFalse(session.closed)

    def test_query_and_commands_keep_native_order_within_one_pump(self):
        session, api = self.open()
        self.message(session, w.WM_CHAR, ord("a"))
        self.raw(session, api, 0x08)
        self.message(session, w.WM_CHAR, 0x08)
        self.raw(session, api, 0x08, True)
        self.message(session, w.WM_CHAR, ord("b"))
        self.raw(session, api, 0x0D)
        seen = []

        def command(query, kind, ctrl):
            seen.append((query, kind))
            return query[:-1] if kind == "BACK_SPACE" else query

        self.assertEqual(session.drain_actions("", command), "b")
        self.assertEqual(seen, [("a", "BACK_SPACE"), ("b", "RET")])

    def test_paste_and_delete_remain_ordered_and_use_existing_modal(self):
        session, api = self.open()
        self.message(session, w.WM_CHAR, ord("a"))
        api.shortcut_held.return_value = True
        api.GetKeyState.side_effect = lambda key: -32768 if key == 0x11 else 0
        self.raw(session, api, 0x56)
        self.message(session, w.WM_CHAR, 0x16)
        self.raw(session, api, 0x56, True)
        api.shortcut_held.return_value = False
        api.GetKeyState.side_effect = None
        api.GetKeyState.return_value = 0
        self.raw(session, api, 0x2E)
        command = Mock(side_effect=["a集合", ""])
        self.assertEqual(session.drain_actions("", command), "")
        self.assertEqual(command.call_args_list[0].args, ("a", "V", True))
        self.assertEqual(command.call_args_list[1].args, ("a集合", "DEL", False))

    def test_backtick_and_middle_dot_switch_modes_without_losing_query(self):
        session, api = self.open()
        for text in ("`", "·"):
            self.message(session, w.WM_CHAR, ord(text))
        command = Mock(side_effect=lambda query, *args: query)
        self.assertEqual(session.drain_actions("集合", command), "集合")
        self.assertEqual(command.call_count, 2)
        command.assert_called_with("集合", "ACCENT_GRAVE", False)

    def test_utf16_surrogate_pair_and_unicode_message(self):
        session, api = self.open()
        for code in (0xD840, 0xDC00):
            self.message(session, w.WM_CHAR, code)
        self.message(session, w.WM_UNICHAR, 0x20001)
        self.assertEqual(session.drain(""), "\U00020000\U00020001")
        self.assertEqual(self.message(session, w.WM_UNICHAR, 0xFFFF), 1)

    def test_ime_committed_middle_dot_also_switches_mode(self):
        session, api = self.open()
        api.strings[w.GCS_RESULTSTR] = "·"
        self.message(session, w.WM_IME_COMPOSITION, lp=w.GCS_RESULTSTR)
        command = Mock(side_effect=lambda query, *args: query)
        self.assertEqual(session.drain_actions("noise", command), "noise")
        command.assert_called_once_with("noise", "ACCENT_GRAVE", False)

    def test_preedit_cancellation_on_close_discards_pending_commit(self):
        session, api = self.open()
        self.message(session, w.WM_IME_STARTCOMPOSITION)
        session.receive(1, "集合")
        session.close()
        api.ImmNotifyIME.assert_called_once_with(session.context, 0x15, 0x4, 0)
        self.assertEqual(session.drain("old"), "old")

    def test_native_callback_exception_does_not_escape_or_log_text(self):
        session, api = self.open()
        api.text.side_effect = RuntimeError("sensitive input")
        self.assertEqual(self.message(session, w.WM_IME_COMPOSITION, lp=w.GCS_RESULTSTR), 10)
        self.assertFalse(session.reacquire())
        self.assertFalse(session.diagnostics)

    def test_candidate_ui_kept_but_default_preedit_ui_hidden(self):
        session, api = self.open()
        self.message(session, w.WM_IME_SETCONTEXT, 1, 0xC000000F)
        api.DefWindowProcW.assert_called_with(session.hwnd, w.WM_IME_SETCONTEXT, 1, 0x4000000F)
        session.caret(100, 600, 1, 24)
        self.message(session, w.WM_IME_NOTIFY, 5)
        self.assertEqual(api.move_caret.call_count, 2)


class WinAPIContractTests(unittest.TestCase):
    def test_system_dlls_and_pointer_width_signatures(self):
        load = Mock(side_effect=lambda *args, **kwargs: Mock())
        with patch.object(w.sys, "platform", "win32"), patch.object(C, "WinDLL", load, create=True), \
                patch.object(C, "WINFUNCTYPE", C.CFUNCTYPE, create=True):
            api = w.WinAPI()
        self.assertEqual([call.args[0] for call in load.call_args_list],
                         ["user32.dll", "imm32.dll", "comctl32.dll", "kernel32.dll"])
        self.assertTrue(all(call.kwargs["winmode"] == 0x800 for call in load.call_args_list))
        self.assertIs(api.GetFocus.restype, C.c_void_p)
        self.assertIs(api.DefSubclassProc.restype, C.c_ssize_t)
        self.assertIs(api.SetWindowSubclass.argtypes[2], C.c_size_t)
        self.assertIs(api.ImmGetCompositionStringW.restype, C.c_int32)

    def test_owner_check_rejects_foreign_thread_process_class_and_focus(self):
        api = w.WinAPI.__new__(w.WinAPI)
        api.GetFocus = Mock(return_value=123)
        api.GetForegroundWindow = Mock(return_value=123)
        api.GetCurrentThreadId = Mock(return_value=1)
        api.GetCurrentProcessId = Mock(return_value=2)

        def owner(hwnd, pid):
            pid._obj.value = 2
            return 1

        def name(hwnd, buffer, size):
            buffer.value = "GHOST_WindowClass"
            return 17

        api.GetWindowThreadProcessId = Mock(side_effect=owner)
        api.GetClassNameW = Mock(side_effect=name)
        self.assertEqual(api.owner_window(), 123)
        for method, value in (("GetCurrentThreadId", 9), ("GetCurrentProcessId", 9),
                              ("GetForegroundWindow", 9), ("GetFocus", None)):
            with patch.object(api, method, return_value=value), self.assertRaises(RuntimeError):
                api.owner_window()
        api.GetClassNameW.side_effect = lambda hwnd, buffer, size: setattr(buffer, "value", "NotBlender")
        with self.assertRaises(RuntimeError):
            api.owner_window()

    def test_altgr_is_not_treated_as_a_command_modifier(self):
        api = w.WinAPI.__new__(w.WinAPI)
        for keys, shortcut in (({0x11}, True), ({0x12}, True), ({0x11, 0x12, 0xA5}, False), ({0x5B}, True)):
            api.GetKeyState = lambda key: -32768 if key in keys else 0
            self.assertEqual(api.shortcut_held(), shortcut)

    def test_windows_struct_sizes_on_64_bit_test_host(self):
        self.assertEqual(C.sizeof(w.POINT), 8)
        self.assertEqual(C.sizeof(w.RECT), 16)
        self.assertEqual(C.sizeof(w.CANDIDATEFORM), 32)
        self.assertEqual(C.sizeof(w.RAWKEYBOARD), 16)
        self.assertEqual(C.sizeof(w.RAWINPUTHEADER), 8 + 2 * C.sizeof(C.c_void_p))

    def test_composition_string_uses_byte_counts_and_utf16(self):
        api = w.WinAPI.__new__(w.WinAPI)
        data = "集合\U00020000".encode("utf-16-le")

        def read(context, kind, buffer, length):
            if buffer is not None:
                C.memmove(buffer, data, len(data))
            return len(data)

        api.ImmGetCompositionStringW = Mock(side_effect=read)
        self.assertEqual(api.text(123, w.GCS_RESULTSTR), "集合\U00020000")
        for invalid in (-1, 3, 2 ** 21):
            api.ImmGetCompositionStringW = Mock(return_value=invalid)
            with self.assertRaises(RuntimeError):
                api.text(123, w.GCS_RESULTSTR)

    def test_caret_client_y_flip_without_double_dpi_scaling(self):
        api = w.WinAPI.__new__(w.WinAPI)

        def rect(hwnd, pointer):
            pointer._obj.right, pointer._obj.bottom = 2400, 1600
            return 1

        api.GetClientRect = Mock(side_effect=rect)
        api.ImmSetCandidateWindow = Mock()
        api.ImmSetCompositionWindow = Mock()
        api.ImmGetContext = Mock(return_value=456)
        api.ImmReleaseContext = Mock()
        api.SetCaretPos = Mock()
        api.move_caret(123, 456, (300, 1300, 2, 48), True)
        candidate = api.ImmSetCandidateWindow.call_args.args[1]._obj
        self.assertEqual((candidate.pos.x, candidate.pos.y), (300, 300))
        self.assertEqual((candidate.area.top, candidate.area.bottom), (252, 300))
        api.SetCaretPos.assert_called_once_with(300, 252)
        api.ImmReleaseContext.assert_called_once_with(123, 456)

    def test_context_released_even_when_composition_read_fails(self):
        api = w.WinAPI.__new__(w.WinAPI)
        api.ImmGetContext = Mock(return_value=456)
        api.ImmReleaseContext = Mock()
        api.text = Mock(side_effect=RuntimeError("read failed"))
        with self.assertRaises(RuntimeError):
            api.composition(123, 456, w.GCS_COMPSTR)
        api.ImmReleaseContext.assert_called_once_with(123, 456)

    def test_foreign_context_not_read(self):
        api = w.WinAPI.__new__(w.WinAPI)
        api.ImmGetContext = Mock(return_value=999)
        api.ImmReleaseContext = Mock()
        api.text = Mock()
        with self.assertRaises(RuntimeError):
            api.composition(123, 456, w.GCS_RESULTSTR)
        api.text.assert_not_called()
        api.ImmReleaseContext.assert_called_once_with(123, 999)


if __name__ == "__main__":
    unittest.main()
