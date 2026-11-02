"""Registered feedback prefs/operator, isolated config, mocked browser only."""
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

import bpy

ROOT = Path(__file__).resolve().parents[1]
assert Path(bpy.utils.user_resource('CONFIG')).resolve() == Path(os.environ['BLENDER_USER_CONFIG']).resolve()
bpy.context.preferences.use_preferences_save = False
spec = importlib.util.spec_from_file_location('NCFeedbackTest', ROOT/'__init__.py', submodule_search_locations=[str(ROOT)])
nc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = nc
spec.loader.exec_module(nc)
nc.register()
addon = bpy.context.preferences.addons.new()
addon.module = nc.ADDON_ID
prefs = addon.preferences
try:
    assert 'placeholder' in bpy.types.UILayout.bl_rna.functions['prop'].parameters
    assert prefs.feedback_text == ''
    sentinel = 'Private draft 测试 ノイズ 노이즈 позиция posición'
    prefs.feedback_text = sentinel
    assert prefs.feedback_text == sentinel
    nc.FEEDBACK_DRAFT = ''
    assert prefs.feedback_text == ''
    nc.FEEDBACK_DRAFT = sentinel
    nc._save_preference_settings()
    assert 'feedback_text' not in nc._load_settings()
    assert sentinel not in nc._settings_path().read_text()
    op = SimpleNamespace(report=Mock())
    browser = Mock(return_value={'FINISHED'})
    proxy = SimpleNamespace(app=bpy.app, context=bpy.context,
                            ops=SimpleNamespace(wm=SimpleNamespace(url_open=browser)))
    with patch.object(nc, 'bpy', proxy):
        assert nc.NODECONSOLE_OT_ReportBug.execute(op, bpy.context) == {'FINISHED'}
        browser.assert_called_once()
        body = parse_qs(urlsplit(browser.call_args.kwargs['url']).query)['body'][0]
        assert sentinel in body and bpy.app.version_string in body
        assert prefs.feedback_text == sentinel
    for value, result, error in (('', {'FINISHED'}, None), ('问题'*10000, {'FINISHED'}, None),
                                  (sentinel, {'CANCELLED'}, None), (sentinel, None, RuntimeError('browser failed'))):
        prefs.feedback_text = value
        browser = Mock(return_value=result, side_effect=error)
        proxy.ops.wm.url_open = browser
        with patch.object(nc, 'bpy', proxy):
            assert nc.NODECONSOLE_OT_ReportBug.execute(op, bpy.context) == {'CANCELLED'}
            assert prefs.feedback_text == value
            if not value or len(value) > 10000:
                browser.assert_not_called()
    assert not hasattr(bpy.context.scene, 'feedback_text')
    print('FEEDBACK_REGRESSION', bpy.app.version_string, 'passed; no real browser/network request')
finally:
    nc.unregister()
    bpy.context.preferences.addons.remove(addon)
