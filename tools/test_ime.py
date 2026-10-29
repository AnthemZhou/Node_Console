"""Unit tests only: these do not prove real system IME composition works."""
import ctypes
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from ime_input import adapter as ime_adapter, session as ime_session
from ime_input.session import Composition, CocoaSession


class CompositionTests(unittest.TestCase):
    def test_preedit_does_not_change_search(self):
        state = Composition()
        state.receive(2, "ji he")
        self.assertEqual(state.drain("Noise "), "Noise ")
        self.assertEqual(state.preedit, "ji he")

    def test_document_commit_replaces_instead_of_duplicating(self):
        state = Composition()
        state.receive(2, "ji he")
        state.receive(4, "集合")
        state.receive(4, "集合信息")
        self.assertEqual(state.drain(""), "集合信息")
        self.assertEqual(state.preedit, "")

    def test_commit_and_new_preedit_keep_event_order(self):
        state = Composition()
        state.receive(4, "集合")
        state.receive(2, "xin")
        self.assertEqual(state.drain(""), "集合")
        self.assertEqual(state.preedit, "xin")

    def test_cancellation_preserves_committed_text(self):
        state = Composition()
        state.receive(2, "ji")
        state.receive(2, "")
        self.assertEqual(state.drain("Noise"), "Noise")
        self.assertEqual(state.preedit, "")

    def test_empty_document_clears_query(self):
        state = Composition()
        state.receive(4, "")
        self.assertEqual(state.drain("集合"), "")

    def test_legacy_append_and_multicodepoint_unicode(self):
        state = Composition()
        state.receive(1, "集合\U00020000")
        self.assertEqual(state.drain("A "), "A 集合\U00020000")

    def test_close_discards_pending_text_and_late_callbacks(self):
        state = Composition()
        state.receive(4, "集合")
        state.receive(3, "diagnostic")
        state.close()
        state.receive(4, "late")
        state.receive(2, "late")
        self.assertEqual(state.drain("before"), "before")
        self.assertFalse(state.diagnostics)
        self.assertEqual(state.preedit, "")


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.library = Mock()
        self.library.nc_ime_start.return_value = 1
        self.library.nc_ime_focused.return_value = 1
        self.library.nc_ime_reacquire.return_value = 1
        self.library.nc_ime_input_source.return_value = b"test.source"
        self.platform_patch = patch.object(ime_session.sys, "platform", "darwin")
        self.library_patch = patch.object(ctypes, "CDLL", return_value=self.library)
        self.platform_patch.start()
        self.library_patch.start()
        self.addCleanup(self.platform_patch.stop)
        self.addCleanup(self.library_patch.stop)

    def test_utf8_callback_and_sync(self):
        session = CocoaSession("lab-only")
        session.callback(4, "集合".encode())
        self.assertEqual(session.drain(""), "集合")
        session.sync("集合")
        self.library.nc_ime_sync.assert_called_once_with("集合".encode())
        session.close()

    def test_double_close_cannot_stop_next_session(self):
        first = CocoaSession("lab-only")
        first.close()
        second = CocoaSession("lab-only")
        first.close()
        self.assertEqual(self.library.nc_ime_stop.call_count, 1)
        second.close()
        self.assertEqual(self.library.nc_ime_stop.call_count, 2)

    def test_closed_session_cannot_touch_native_focus(self):
        session = CocoaSession("lab-only")
        session.close()
        session.sync("late")
        session.caret(1, 2, 3, 4)
        self.assertFalse(session.focused())
        self.assertFalse(session.reacquire())
        self.library.nc_ime_sync.assert_not_called()
        self.library.nc_ime_caret.assert_not_called()
        self.library.nc_ime_reacquire.assert_not_called()

    def test_failed_start_does_not_stop_another_owner(self):
        self.library.nc_ime_start.return_value = 0
        with self.assertRaisesRegex(RuntimeError, "Could not acquire input focus"):
            CocoaSession("lab-only")
        self.library.nc_ime_stop.assert_not_called()


class FakeSession(Composition):
    def __init__(self, library):
        super().__init__()
        self.library = library
        self.close_calls = 0
        self.sync = Mock()
        self.caret = Mock()
        self.reacquire = Mock(return_value=True)

    def close(self):
        self.close_calls += 1
        super().close()


class AdapterTests(unittest.TestCase):
    def setUp(self):
        nc = self.nc = SimpleNamespace(ACTIVE_CONSOLE_OPERATOR=None)

        class Console:
            def invoke(self, context, event):
                if nc.ACTIVE_CONSOLE_OPERATOR is not None:
                    nc.ACTIVE_CONSOLE_OPERATOR._finish(context, {"CANCELLED"})
                nc.ACTIVE_CONSOLE_OPERATOR = self
                self._query = ""
                self._refresh_query_results = Mock()
                self._tag_owner_redraw = Mock()
                self._owns_context = Mock(return_value=True)
                self.original_events = []
                self.finished = False
                self.hidden = False
                self.registered_modal = True
                return {"RUNNING_MODAL"}

            def modal(self, context, event):
                self.original_events.append(event.type)
                if event.type == "BACK_SPACE":
                    self._query = self._query[:-1]
                if event.type == "ESC":
                    return self._finish(context, {"CANCELLED"})
                if event.type == "RET":
                    self._hide_console(context)
                return {"RUNNING_MODAL"}

            def _finish(self, context, result):
                self.finished = True
                if nc.ACTIVE_CONSOLE_OPERATOR is self:
                    nc.ACTIVE_CONSOLE_OPERATOR = None
                return result

            def _hide_console(self, context):
                self.hidden = True

            def _draw_callback(self, context):
                self._ime_caret_rect = (1, 2, 3, 4)

        self.console = Console
        nc.ENS_AddNodeByEnglishSearch = Console
        self.original_modal = Console.modal
        self.context = SimpleNamespace(window=object(), window_manager=SimpleNamespace(
            event_timer_add=Mock(side_effect=lambda *a, **kw: object()), event_timer_remove=Mock()))
        self.factory_patch = patch.object(ime_adapter, "CocoaSession", side_effect=FakeSession)
        self.factory = self.factory_patch.start()
        self.addCleanup(self.factory_patch.stop)
        self.clock = patch.object(ime_adapter.time, "monotonic", return_value=1.0)
        self.now = self.clock.start()
        self.addCleanup(self.clock.stop)
        self.log = Mock()
        self.uninstall = ime_adapter.install(nc, "lab-only", self.log)
        self.addCleanup(lambda: self.uninstall(self.context))

    def open(self):
        op = self.console()
        self.assertEqual(op.invoke(self.context, SimpleNamespace()), {"RUNNING_MODAL"})
        return op

    def event(self, op, kind="TIMER"):
        # Match real Blender RNA events: no .timer attribute is available.
        return op.modal(self.context, SimpleNamespace(type=kind))

    def test_focus_failure_keeps_original_search_usable(self):
        self.factory.side_effect = RuntimeError("no key window")
        op = self.open()
        self.assertTrue(op.registered_modal)
        self.assertFalse(op.finished)
        self.assertEqual(self.event(op, "BACK_SPACE"), {"RUNNING_MODAL"})
        self.assertIsNone(op._ime_session)
        self.assertEqual(self.event(op, "ESC"), {"CANCELLED"})

    def test_timer_failure_closes_receiver_and_keeps_original_search(self):
        self.context.window_manager.event_timer_add.side_effect = RuntimeError("timer unavailable")
        op = self.open()
        self.assertIsNone(op._ime_session)
        self.assertEqual(self.event(op), {"RUNNING_MODAL"})
        self.assertEqual(self.event(op, "ESC"), {"CANCELLED"})

    def test_reopen_closes_old_session_before_acquiring_new(self):
        first = self.open()
        session = first._ime_session
        second = self.open()
        self.assertTrue(first.finished)
        self.assertEqual(session.close_calls, 1)
        first._finish(self.context, {"CANCELLED"})
        self.assertFalse(second._ime_session.closed)
        self.assertIs(self.nc.ACTIVE_CONSOLE_OPERATOR, second)

    def test_preedit_redraw_without_search(self):
        op = self.open()
        op._ime_session.receive(2, "ji he")
        self.event(op)
        self.assertEqual(op._ime_preedit, "ji he")
        self.assertEqual(op._query, "")
        op._refresh_query_results.assert_not_called()
        op._tag_owner_redraw.assert_called_once()

    def test_commit_refreshes_once_and_updates_query(self):
        op = self.open()
        op._ime_session.receive(4, "集合")
        self.event(op)
        self.assertEqual(op._query, "集合")
        op._refresh_query_results.assert_called_once()

    def test_idle_bridge_timer_does_not_redraw_or_step_drag(self):
        op = self.open()
        for _ in range(100):
            self.event(op)
        self.assertEqual(op.original_events, [])
        op._tag_owner_redraw.assert_not_called()
        self.now.return_value = 1.21
        self.event(op)
        self.assertEqual(op.original_events, ["TIMER"])

    def test_animation_ticks_are_capped_without_delay_on_drag_start(self):
        op = self.open()
        op._shortcut_animation_timer = object()
        self.event(op)
        self.assertEqual(op.original_events, ["TIMER"])
        self.now.return_value = 1.005
        self.event(op)
        self.assertEqual(op.original_events, ["TIMER"])
        self.now.return_value = 1.02
        self.event(op)
        self.assertEqual(op.original_events, ["TIMER", "TIMER"])

    def test_backspace_keeps_native_document_in_sync(self):
        op = self.open()
        op._query = "集合"
        self.event(op, "BACK_SPACE")
        op._ime_session.sync.assert_called_with("集")

    def test_escape_cleanup_is_idempotent(self):
        op = self.open()
        session = op._ime_session
        self.assertEqual(self.event(op, "ESC"), {"CANCELLED"})
        op._finish(self.context, {"CANCELLED"})
        self.assertEqual(session.close_calls, 1)
        self.context.window_manager.event_timer_remove.assert_called_once()

    def test_window_deactivation_discards_preedit(self):
        op = self.open()
        op._ime_session.receive(2, "ji")
        self.assertEqual(self.event(op, "WINDOW_DEACTIVATE"), {"CANCELLED"})
        self.assertIsNone(op._ime_session)
        self.assertEqual(op._ime_preedit, "")

    def test_lost_focus_closes_instead_of_stealing_other_field(self):
        op = self.open()
        op._ime_session.reacquire.return_value = False
        self.assertEqual(self.event(op), {"CANCELLED"})
        self.assertTrue(op.finished)

    def test_placement_releases_receiver_before_mouse_operation(self):
        op = self.open()
        session = op._ime_session
        self.event(op, "RET")
        self.assertTrue(op.hidden)
        self.assertTrue(session.closed)
        self.assertIsNone(op._ime_timer)

    def test_draw_updates_candidate_caret(self):
        op = self.open()
        op._draw_callback(self.context)
        op._ime_session.caret.assert_called_once_with(1, 2, 3, 4)

    def test_uninstall_restores_methods_and_closes_active_session(self):
        op = self.open()
        session = op._ime_session
        self.uninstall(self.context)
        self.assertIs(self.console.modal, self.original_modal)
        self.assertTrue(session.closed)


if __name__ == "__main__":
    unittest.main()
