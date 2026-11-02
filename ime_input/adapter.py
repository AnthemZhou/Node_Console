"""Keep the GPU interface while routing composition through the system IME."""
import time

from .session import CocoaSession


class _CommandEvent:
    def __init__(self, source, kind, ctrl=False):
        self.source = source
        self.type, self.value, self.unicode = kind, "PRESS", ""
        self.ctrl, self.alt, self.oskey, self.shift = ctrl, False, False, False

    def __getattr__(self, name):
        return getattr(self.source, name)


def install(nc, library, log, session_factory=None):
    console = nc.ENS_AddNodeByEnglishSearch
    originals = {name: getattr(console, name) for name in
                 ("invoke", "modal", "_finish", "_hide_console", "_draw_callback")}

    def close(self, context):
        session = getattr(self, "_ime_session", None)
        self._ime_session = None
        self._ime_preedit = ""
        timer = getattr(self, "_ime_timer", None)
        self._ime_timer = None
        try:
            if session is not None:
                session.close()
                log("ime_closed")
        finally:
            if timer is not None:
                try:
                    context.window_manager.event_timer_remove(timer)
                except ReferenceError:
                    pass

    def drain(self, context, event):
        session = getattr(self, "_ime_session", None)
        if session is None:
            return
        previous = self._ime_preedit
        while session.diagnostics:
            log("ime_key", detail=session.diagnostics.popleft())
        previous_query = self._query
        refreshed = (previous_query, previous)
        outcome = None

        def command(query, kind, ctrl):
            nonlocal outcome, refreshed
            if refreshed != (query, session.preedit):
                self._query = query
                self._ime_preedit = session.preedit
                self._refresh_query_results()
                refreshed = (query, session.preedit)
            outcome = originals["modal"](self, context, _CommandEvent(event, kind, ctrl))
            return self._query

        if hasattr(session, "drain_actions"):
            self._query = session.drain_actions(self._query, command)
        else:
            self._query = session.drain(self._query)
        if getattr(self, "_ime_session", None) is not session:
            return outcome
        self._ime_preedit = session.preedit
        if refreshed != (self._query, self._ime_preedit):
            self._refresh_query_results()
        if previous_query != self._query:
            log("ime_commit", query=self._query)
        if previous_query != self._query or previous != self._ime_preedit:
            log("ime_preedit", text=self._ime_preedit)
            self._tag_owner_redraw(context)
        return outcome

    def invoke(self, context, event):
        result = originals["invoke"](self, context, event)
        if result != {"RUNNING_MODAL"}:
            return result
        self._ime_preedit = ""
        self._ime_next_tick = time.monotonic() + 0.2
        self._ime_tick_interval = 0.2
        try:
            self._ime_session = (session_factory() if session_factory is not None else
                                 CocoaSession(library() if callable(library) else library))
            self._ime_session.sync(self._query)
            self._ime_timer = context.window_manager.event_timer_add(0.02, window=context.window)
            log("ime_started")
        except Exception as exc:
            close(self, context)
            log("ime_error", message=str(exc))
            # Keep the original modal search usable if the native backend is unavailable.
        return result

    def modal(self, context, event):
        # Focus loss wins over any pending commit/Enter from a departing window.
        if event.type == "WINDOW_DEACTIVATE":
            return self._finish(context, {"CANCELLED"})
        outcome = drain(self, context, event)
        if outcome is not None and outcome != {"RUNNING_MODAL"}:
            return outcome
        session = getattr(self, "_ime_session", None)
        if event.type == "TIMER" and session is not None:
            if nc.ACTIVE_CONSOLE_OPERATOR is not self:
                return self._finish(context, {"CANCELLED"})
            if session is not None and not session.reacquire():
                return self._finish(context, {"CANCELLED"})
            # Blender RNA events have no timer identity. Drain every tick, but keep
            # idle redraws at the original rate and animate only while dragging.
            now = time.monotonic()
            interval = 1 / 60 if getattr(self, "_shortcut_animation_timer", None) else 0.2
            if now < self._ime_next_tick and interval == self._ime_tick_interval:
                return {"RUNNING_MODAL"}
            self._ime_tick_interval = interval
            self._ime_next_tick = now + interval
        result = originals["modal"](self, context, event)
        session = getattr(self, "_ime_session", None)
        if session is not None and result == {"RUNNING_MODAL"}:
            session.sync(self._query)
            if not session.reacquire():
                return self._finish(context, {"CANCELLED"})
        return result

    def finish(self, context, result):
        try:
            close(self, context)
        finally:
            result = originals["_finish"](self, context, result)
        return result

    def hide(self, context):
        close(self, context)
        return originals["_hide_console"](self, context)

    def draw(self, context):
        originals["_draw_callback"](self, context)
        session = getattr(self, "_ime_session", None)
        caret = getattr(self, "_ime_caret_rect", None)
        if session is not None and caret and self._owns_context(context):
            try:
                session.caret(*caret)
            except Exception:
                close(self, context)
                log("ime_error", message="Could not update native input position")

    console.invoke = invoke
    console.modal = modal
    console._finish = finish
    console._hide_console = hide
    console._draw_callback = draw

    def uninstall(context):
        active = nc.ACTIVE_CONSOLE_OPERATOR
        if active is not None:
            active._finish(context, {"CANCELLED"})
        for name, method in originals.items():
            setattr(console, name, method)

    return uninstall
