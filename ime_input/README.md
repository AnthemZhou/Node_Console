# Native text input

Node Console 1.4.0 uses a non-drawing, mouse-transparent Cocoa `NSTextView` for
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

Only macOS installs the input adapter. Other platforms keep their original
input handling. Missing/corrupt resources, failed native loads and failed focus
acquisition leave the standard input path available. Installed logging records
backend failures, never typed queries, marked text or keystrokes.

## Verification

Real macOS Pinyin composition, candidate confirmation, Esc cancellation,
reopening and Enter/mouse node placement were manually confirmed on Apple
Silicon with Blender 5.2.2 LTS. Unit tests are separate and do not prove actual
input-method behavior. Intel Mac, Windows/Linux native composition, third-party
IMEs, long-preedit editing and multi-monitor candidate placement are not certified.

The 20ms input timer drains changes, while elapsed-time gating retains 200ms
idle redraws and bounds drag animation ticks. Blender RNA events do not expose
their originating timer, so timer object comparisons must not be used.

Run `python3 -m unittest tools.test_ime tools.test_ime_resource` for isolated
lifecycle, fallback, composition and resource tests. Blender package-install and
hot-reload tests use factory startup and private configuration directories.
