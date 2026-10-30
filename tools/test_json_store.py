"""User-data cache isolation and atomic-write failure regressions, without Blender."""
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from json_store import JsonStore


class JsonStoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'settings.json'
        self.store = JsonStore()
        self.initial = {'favorites': ['one'], 'nested': {'value': [1]}, 'future': 42}
        self.path.write_text(json.dumps(self.initial), encoding='utf-8')

    def test_unchanged_file_parsed_once(self):
        with patch('json_store.json.load', wraps=json.load) as load:
            for _ in range(20):
                self.assertEqual(self.store.read(self.path, 'favorites'), ['one'])
            self.assertEqual(load.call_count, 1)

    def test_mutable_values_are_isolated(self):
        data = self.store.read(self.path)
        data['nested']['value'].append(2)
        self.store.read(self.path, 'favorites').clear()
        self.assertEqual(self.store.read(self.path), self.initial)
        self.store.write(self.path, data)
        data['nested']['value'].append(3)
        self.assertEqual(self.store.read(self.path, 'nested'), {'value': [1, 2]})

    def test_missing_default_is_isolated(self):
        fallback = {'values': []}
        self.store.read(self.path, 'missing', fallback)['values'].append(1)
        self.assertEqual(fallback, {'values': []})

    def test_nested_read_copies_only_requested_value(self):
        self.assertEqual(self.store.read(self.path, ('nested', 'value')), [1])
        self.store.read(self.path, ('nested', 'value')).clear()
        self.assertEqual(self.store.read(self.path, ('nested', 'value')), [1])
        self.assertEqual(self.store.read(self.path, ('future', 'bad'), []), [])

    def test_projection_result_is_isolated(self):
        data = self.store.read(self.path, project=lambda data: {'subset': data['nested']})
        data['subset']['value'].append(3)
        self.assertEqual(self.store.read(self.path), self.initial)

    def test_external_same_size_edit_and_replace(self):
        self.store.read(self.path)
        stamp = self.path.stat()
        self.path.write_text(json.dumps(dict(self.initial, future=43)), encoding='utf-8')
        os.utime(self.path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        self.assertEqual(self.store.read(self.path, 'future'), 43)
        replacement = self.path.with_suffix('.new')
        replacement.write_text(json.dumps(dict(self.initial, future=44)), encoding='utf-8')
        os.utime(replacement, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        replacement.replace(self.path)
        self.assertEqual(self.store.read(self.path, 'future'), 44)

    def test_path_change_delete_recreate_and_clear(self):
        first_revision = self.store.refresh(self.path)
        other = self.path.with_name('other.json')
        self.assertEqual(self.store.read(other), {})
        self.store.write(other, {'new': True})
        self.assertEqual(self.store.read(other), {'new': True})
        self.assertEqual(self.store.read(self.path), self.initial)
        self.path.unlink()
        self.assertEqual(self.store.read(self.path), {})
        self.path.write_text('{"new": false}', encoding='utf-8')
        self.assertEqual(self.store.read(self.path), {'new': False})
        self.store.clear()
        self.assertGreater(self.store.refresh(self.path), first_revision)
        self.assertEqual(self.store.read(self.path), {'new': False})

    def test_invalid_json_never_overwritten_and_recovers(self):
        for invalid in ('{broken', '[]', 'null'):
            self.path.write_text(invalid, encoding='utf-8')
            self.assertEqual(self.store.read(self.path), {})
            with self.assertRaises(OSError):
                self.store.write(self.path, {'would': 'erase data'})
            self.assertEqual(self.path.read_text(), invalid)
        self.path.write_text(json.dumps(self.initial), encoding='utf-8')
        self.assertEqual(self.store.read(self.path), self.initial)

    def test_replace_failure_keeps_disk_and_cache(self):
        self.store.read(self.path)
        with patch('json_store.os.replace', side_effect=PermissionError('denied')):
            with self.assertRaises(PermissionError):
                self.store.write(self.path, {'new': True})
        self.assertEqual(json.loads(self.path.read_text()), self.initial)
        self.assertEqual(self.store.read(self.path), self.initial)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_flush_failure_keeps_original_and_cleans_temp(self):
        with patch('json_store.os.fsync', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.store.write(self.path, {'new': True})
        self.assertEqual(self.store.read(self.path), self.initial)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_serialization_failure_keeps_original(self):
        with self.assertRaises(TypeError):
            self.store.write(self.path, {'bad': object()})
        self.assertEqual(self.store.read(self.path), self.initial)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_preserves_mode_and_symlink(self):
        self.path.chmod(0o640)
        link = self.path.with_name('link.json')
        link.symlink_to(self.path)
        self.store.write(link, self.initial)
        self.assertTrue(link.is_symlink())
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o640)
        self.assertEqual(self.store.read(link), self.initial)

    def test_change_during_write_is_not_overwritten(self):
        original_fsync = os.fsync

        def concurrent_write(fd):
            original_fsync(fd)
            self.path.write_text('{"external": true}', encoding='utf-8')

        with patch('json_store.os.fsync', side_effect=concurrent_write):
            with self.assertRaises(OSError):
                self.store.write(self.path, {'stale': True})
        self.assertEqual(self.store.read(self.path), {'external': True})
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_update_copies_only_changes_and_preserves_unknown_fields(self):
        from copy import deepcopy
        changes = {'favorites': ['new'], 'shortcut_tree_meta': {'new': ['GeometryNodeTree']}}
        self.store.refresh(self.path)
        with patch('json_store.deepcopy', wraps=deepcopy) as copy:
            self.store.update(self.path, changes)
        copy.assert_called_once_with(changes)
        expected = dict(self.initial, **deepcopy(changes))
        changes['favorites'].append('not saved')
        self.assertEqual(self.store.read(self.path), expected)

    def test_identical_update_does_not_write_or_change_revision(self):
        revision = self.store.refresh(self.path)
        stamp = self.path.stat()
        with patch('json_store.os.replace') as replace:
            self.store.update(self.path, {'favorites': ['one']})
            self.store.update(self.path, {})
        replace.assert_not_called()
        self.assertEqual(self.store.revision, revision)
        self.assertEqual(self.path.stat(), stamp)

    def test_update_reads_external_changes_before_merging(self):
        self.store.refresh(self.path)
        self.path.write_text(json.dumps(dict(self.initial, external=42)), encoding='utf-8')
        self.store.update(self.path, {'favorites': ['new']})
        self.assertEqual(self.store.read(self.path), dict(self.initial, external=42, favorites=['new']))

    def test_invalid_json_is_not_overwritten_by_update(self):
        self.path.write_text('{broken', encoding='utf-8')
        for changes in ({}, {'favorites': []}):
            with self.assertRaises(OSError):
                self.store.update(self.path, changes)
        self.assertEqual(self.path.read_text(), '{broken')

    def test_failed_update_does_not_publish_partial_changes(self):
        for failure in ('fsync', 'replace'):
            with patch('json_store.os.' + failure, side_effect=OSError('failed')):
                with self.assertRaises(OSError):
                    self.store.update(self.path, {'favorites': ['new'], 'added': True})
            self.assertEqual(self.store.read(self.path), self.initial)
            self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_external_edit_during_update_is_not_overwritten(self):
        original_fsync = os.fsync

        def concurrent_write(fd):
            original_fsync(fd)
            self.path.write_text('{"external": true}', encoding='utf-8')

        with patch('json_store.os.fsync', side_effect=concurrent_write):
            with self.assertRaises(OSError):
                self.store.update(self.path, {'favorites': ['new']})
        self.assertEqual(self.store.read(self.path), {'external': True})
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])


if __name__ == '__main__':
    unittest.main()
