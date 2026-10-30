# Native text input

On macOS Node Console uses a non-drawing, mouse-transparent Cocoa `NSTextView` for
system composition while retaining the existing GPU field and modal workflow.
No Blender ABI access, method swizzling, global keyboard hooks, input-source
switching, network service or clipboard-based composition is used.

## Build and packaging

On macOS with Xcode Command Line Tools, run `python3 tools/build_ime.py`, then
`python3 tools/build_local_release.py --package-only` from the repository root.
The build compiles arm64/x86_64, ad-hoc signs and verifies the universal library,
and writes the version, source hash, binary hash and base64 payload to
`ime_input/macos.json`. The source is `ime_input/ime_cocoa.m`; all corresponding
source and build scripts are included in the Git tag, under the repository GPL.

The JSON envelope keeps the ZIP compatible with the existing 1.3.x updater's
allowed file extensions. It is not downloaded separately or compiled on the
user's machine. The receiver is decoded and SHA256-checked on first use, then
atomically cached in `~/Library/Caches/NodeConsole/IME/<sha256>/`. Checksums detect
corruption, not an untrusted release. Versioned library paths and Objective-C
class names avoid collisions between releases kept loaded during hot updates.

macOS and Windows install the input adapter. Linux keeps its original
input handling. Missing/corrupt resources, failed native loads and failed focus
acquisition leave the standard input path available. Installed logging records
backend failures, never typed queries, marked text or keystrokes.

## Verification

Real macOS Pinyin composition, candidate confirmation, Esc cancellation,
reopening and Enter/mouse node placement were manually confirmed on Apple
Silicon with Blender 5.2.2 LTS. Unit tests are separate and do not prove actual
input-method behavior. A user confirmed committed Chinese and node search on
Windows; OS, Blender and IME versions were not recorded. Intel Mac, Linux native
composition, third-party IMEs, long-preedit editing and multi-monitor candidate
placement are not certified. Complete Windows focus/placement coverage and the
1.4.2 one-scaled-pixel CJK baseline adjustment still need live visual validation.

## Windows backend (introduced in 1.4.1)

`windows.py` uses Python's bundled ctypes with system `user32`, `imm32` and
`comctl32`, loaded from System32. There is no extra DLL download or compiler.
It checks the focused window's class, process and UI thread before attaching a
`SetWindowSubclass` callback. The default IMM context is borrowed only if the
window had no context; its previous association is restored on exit. Input
language, conversion mode, keymaps and global hooks are never modified.

The receiver consumes `WM_IME_COMPOSITION` preedit/result UTF-16 strings and lets
the system draw candidates. Blender independently translates raw keyboard input,
so text keys are consumed from `WM_INPUT` while normal text comes from `WM_CHAR`.
Composition navigation/confirmation stays with the IME. Non-composing editing,
Enter/Esc, paste and mode changes are queued in order with text and dispatched
through the existing modal methods, including selection and placement behavior.
Mouse, non-keyboard devices and unrelated modifier shortcuts keep their route.
The timer only drains events; native callbacks do not access bpy or log queries.

Candidate rectangles use the DPI-aware client coordinates, with Y flipped from
Blender's bottom-origin drawing coordinates. This still requires real testing
on Windows 10/11 with Microsoft Pinyin, display scaling and multiple monitors.
Unit tests on macOS are not evidence that Windows IME or TSF compatibility works.

To test in an isolated Windows Blender process without installing over a stable
add-on or writing user preferences, run from this checkout:

```powershell
py tools/run_windows_ime_lab.py --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
```

This creates a disposable Geometry Nodes scene and private configuration; closing
that Blender process removes the temporary config. No input text is logged.
Use this checklist for broader live validation:

- Shift+A, Microsoft Pinyin `jihe`, choose `集合`, then Enter to create/place.
- During `zaobo` composition Esc cancels only preedit; the next Esc closes search.
- Reopen at least ten times; switch Chinese/English and windows without stuck focus.
- Type quickly, backspace, Ctrl+V, Delete, arrows, ` / middle dot, click results and drag shortcuts.
- Check candidates at 100%, 150%, 200% and on another monitor; check native Blender text fields after closing.
- Disable/re-enable the add-on and confirm Shift+P, Node Wrangler Ctrl+T and custom keymaps remain intact.

API and event-routing references:
- [Microsoft: WM_IME_COMPOSITION](https://learn.microsoft.com/en-us/windows/win32/intl/wm-ime-composition)
- [Microsoft: context association and restoration](https://learn.microsoft.com/en-us/windows/win32/api/imm/nf-imm-immassociatecontext)
- [Microsoft: window subclass lifetime/thread restrictions](https://learn.microsoft.com/en-us/windows/win32/api/commctrl/nf-commctrl-setwindowsubclass)
- [Blender: Win32 raw input and IME event dispatch](https://github.com/blender/blender/blob/main/intern/ghost/intern/GHOST_SystemWin32.cc)

The 20ms input timer drains changes, while elapsed-time gating retains 200ms
idle redraws and bounds drag animation ticks. Blender RNA events do not expose
their originating timer, so timer object comparisons must not be used.

Run `python3 -m unittest tools.test_ime tools.test_windows_ime tools.test_ime_resource` for isolated
lifecycle, fallback, composition and resource tests. Blender package-install and
hot-reload tests use factory startup and private configuration directories.
