# Release Checklist

Maintainer documentation. Keep the root README focused on current features and
usage. Put version-specific changes in CHANGELOG and GitHub release notes, and
detailed measurements and verification limits in PERFORMANCE.md.

## Version and Metadata

- Set `ADDON_VERSION` and `bl_info["version"]` in `__init__.py`. For a prerelease
  such as `1.6.0-beta.1`, keep the full string in `ADDON_VERSION` and the numeric
  tuple `(1, 6, 0)` in `bl_info`.
- Add the brief English update highlight to `addon_updater.RELEASE_HIGHLIGHTS`
  and its Chinese translation to `UI_TEXT_ZH`.
- Add a CHANGELOG section and preserve its summary comment in the GitHub release
  body, for example:

  ```html
  <!-- node-console-summary: {"zh":"首次搜索提速","en":"Faster first search"} -->
  ```

- Summary limits are 32 Chinese / 72 English characters; prefer shorter wording.
  Updaters from 1.4.5 can read this metadata before installation. Missing or invalid
  summaries fall back to known highlights or "See release notes" without changing
  release eligibility.
- Update the current README badge, version and download links without adding a
  release history. Preserve user-provided images and the language sections.

## Build and Test

On macOS with the Xcode command-line tools installed:

```sh
python3 tools/build_ime.py
python3 tools/build_local_release.py --package-only
```

Rebuild the versioned macOS input resource even when its source is unchanged;
the versioned native class names support hot reload. The package must be named
`Node_Console_<version>.zip` and contain the `Node_Console/` directory. GitHub's
automatic Source code archives are not installation packages.

Run the relevant unit tests and Blender regressions, including package
installation and upgrade. Use `tools/run_isolated_blender.py` with private
configuration; never save test preferences into the user's Blender profile.
Keep generated reports under ignored `build/`. Exclude private assets, user data
and local validation reports from commits and installation packages.

## Publish and Verify

- Commit the intended changes and create the matching `v<version>` tag. Push only
  when publication is requested.
- Attach `Node_Console_<version>.zip` and the corresponding release notes.
- Stable releases use a plain version tag and are not marked Pre-release. For
  Beta/RC releases, use a full tag such as `v1.6.0-beta.1` or `v1.6.0-rc.1` and
  mark the GitHub release as **Pre-release**. Changing only the title is not enough.
- Download the uploaded asset and compare its SHA256 with the tested local ZIP.
- Check the updater can discover the release, recognize its channel and display
  its localized summary. Changing the Beta filter must not install a version.
- Keep the published package and tag intact during later documentation-only edits.
