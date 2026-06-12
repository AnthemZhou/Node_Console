from __future__ import annotations

import ast
import ctypes
import ctypes.util
import hashlib
import json
import math
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import blf
import bpy
import gpu
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
from bpy.types import AddonPreferences, Operator, SpaceNodeEditor
from gpu_extras.batch import batch_for_shader


ADDON_VERSION = "0.8.25"


bl_info = {
    "name": "Node Console",
    "author": "Anthem",
    "version": (0, 8, 25),
    "blender": (5, 1, 2),
    "location": "Node Editor > Shift A",
    "description": "Language-independent custom node launcher with favorite boosting.",
    "category": "Node",
}


ADDON_ID = __name__
KEYMAP_ITEMS = []
NODE_SEARCH_ENTRIES: list["NodeSearchEntry"] = []
MENU_ENTRY_CACHE: dict[str, list[tuple[str, str, str, str, tuple[tuple[str, str], ...]]]] = {}
SEARCH_INDEX_MEMORY_KEYS: set[str] = set()
TRANSLATION_LABEL_CACHE: dict[tuple[str, str | None], str] = {}
NODE_CLASS_CACHE: list[type] | None = None
BACKGROUND_ASSET_INDEX = None

FONT_ID = 0
MAX_RESULTS = 12
PANEL_WIDTH = 404
SEARCH_HEIGHT = 23
ROW_HEIGHT = 26
PANEL_PADDING = 8
SHORTCUT_HEIGHT = 23
SHORTCUT_GAP = 4
CONTEXT_MENU_WIDTH = 190
CONTEXT_MENU_ROW_HEIGHT = 30
PANEL_BACKGROUND = (0.095, 0.095, 0.1, 0.98)
FIELD_BACKGROUND = (0.12, 0.12, 0.125, 1.0)
BORDER_COLOR = (0.24, 0.24, 0.25, 0.92)
HIGHLIGHT_COLOR = (0.31, 0.31, 0.31, 0.98)
HIGHLIGHT_BORDER_COLOR = (0.38, 0.38, 0.38, 0.85)
TEXT_COLOR = (0.88, 0.88, 0.9, 1.0)
MUTED_TEXT_COLOR = (0.58, 0.58, 0.6, 1.0)
SECONDARY_TEXT_COLOR = (0.435, 0.435, 0.45, 1.0)
NODE_TYPE_COLORS = {
    "attribute": (0.12, 0.17, 0.36, 1.0),
    "input": (0.56, 0.23, 0.34, 1.0),
    "color": (0.44, 0.46, 0.15, 1.0),
    "output": (0.20, 0.20, 0.20, 1.0),
    "converter": (0.21, 0.43, 0.58, 1.0),
    "texture": (0.48, 0.27, 0.11, 1.0),
    "geometry": (0.19, 0.50, 0.41, 1.0),
    "vector": (0.28, 0.27, 0.58, 1.0),
    "none": (0.24, 0.34, 0.18, 1.0),
}
CATEGORY_COLOR_FALLBACK = NODE_TYPE_COLORS["none"]
GEOMETRY_COLOR_KEYS = {"geometry", "mesh", "curve", "point", "points", "volume", "instances", "instance", "hair", "grease", "pencil", "grease pencil"}
CONVERTER_COLOR_KEYS = {"math", "utilities", "converter", "rotation"}
VECTOR_COLOR_KEYS = {"vector", "uv"}
NODE_COLOR_TAG_TYPES = {
    "ATTRIBUTE": "attribute",
    "INPUT": "input",
    "COLOR": "color",
    "OUTPUT": "output",
    "CONVERTER": "converter",
    "TEXTURE": "texture",
    "GEOMETRY": "geometry",
    "VECTOR": "vector",
    "NONE": "none",
}
SETTINGS_FILENAME = "node_console_settings.json"
BUNDLED_CACHE_FILENAME = "node_console_builtin_cache.json"


@dataclass(frozen=True)
class NodeSearchEntry:
    identifier: str
    category: str
    english: str
    chinese: str
    label: str
    description: str
    kind: str
    node_type: str = ""
    asset_path: str = ""
    asset_name: str = ""
    asset_color_tag: str = ""
    search_text: str = ""
    settings: tuple[tuple[str, str], ...] = ()


NODE_ENTRY_BY_ID: dict[str, NodeSearchEntry] = {}


def _clear_search_caches():
    global NODE_CLASS_CACHE
    MENU_ENTRY_CACHE.clear()
    TRANSLATION_LABEL_CACHE.clear()
    NODE_CLASS_CACHE = None


def _safe_identifier(prefix: str, *parts: str) -> str:
    text = "_".join(part for part in parts if part)
    text = re.sub(r"[^A-Za-z0-9_]+", "_", text).strip("_")
    return f"{prefix}_{text[:80]}"


def _normalize(text: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", " ", text.lower()).replace("_", " ").strip()


def _camel_words(text: str) -> str:
    text = re.sub(r"(Node|Shader|Function|Geometry|Compositor|Texture)", " ", text)
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    return _normalize(text)


def _compact(text: str) -> str:
    return _normalize(text).replace(" ", "")


PINYIN_TEXT_CACHE: dict[str, str] = {}
PINYIN_TRANSFORM_READY: bool | None = None
PINYIN_CF = None
PINYIN_MANDARIN_LATIN = None
PINYIN_STRIP_MARKS = None
PINYIN_CHAR_TABLE = {'三': 'san',
 '上': 'shang',
 '下': 'xia',
 '不': 'bu',
 '与': 'yu',
 '世': 'shi',
 '个': 'ge',
 '中': 'zhong',
 '串': 'chuan',
 '临': 'lin',
 '为': 'wei',
 '义': 'yi',
 '乒': 'ping',
 '乓': 'pang',
 '乘': 'cheng',
 '二': 'er',
 '于': 'yu',
 '云': 'yun',
 '五': 'wu',
 '交': 'jiao',
 '产': 'chan',
 '亮': 'liang',
 '件': 'jian',
 '伊': 'yi',
 '传': 'chuan',
 '估': 'gu',
 '伽': 'jia',
 '位': 'wei',
 '体': 'ti',
 '何': 'he',
 '余': 'yu',
 '例': 'li',
 '信': 'xin',
 '修': 'xiu',
 '倍': 'bei',
 '倒': 'dao',
 '值': 'zhi',
 '倾': 'qing',
 '偏': 'pian',
 '偶': 'ou',
 '储': 'chu',
 '像': 'xiang',
 '元': 'yuan',
 '充': 'chong',
 '光': 'guang',
 '入': 'ru',
 '公': 'gong',
 '具': 'ju',
 '内': 'nei',
 '再': 'zai',
 '减': 'jian',
 '几': 'ji',
 '凸': 'tu',
 '凹': 'ao',
 '出': 'chu',
 '分': 'fen',
 '切': 'qie',
 '列': 'lie',
 '删': 'shan',
 '到': 'dao',
 '制': 'zhi',
 '前': 'qian',
 '剪': 'jian',
 '功': 'gong',
 '加': 'jia',
 '动': 'dong',
 '包': 'bao',
 '化': 'hua',
 '匹': 'pi',
 '区': 'qu',
 '半': 'ban',
 '单': 'dan',
 '卡': 'ka',
 '卷': 'juan',
 '厚': 'hou',
 '原': 'yuan',
 '去': 'qu',
 '参': 'can',
 '叉': 'cha',
 '双': 'shuang',
 '反': 'fan',
 '发': 'fa',
 '取': 'qu',
 '变': 'bian',
 '叠': 'die',
 '口': 'kou',
 '号': 'hao',
 '合': 'he',
 '名': 'ming',
 '后': 'hou',
 '向': 'xiang',
 '否': 'fou',
 '含': 'han',
 '启': 'qi',
 '吸': 'xi',
 '告': 'gao',
 '周': 'zhou',
 '命': 'ming',
 '和': 'he',
 '哈': 'ha',
 '喜': 'xi',
 '器': 'qi',
 '噪': 'zao',
 '四': 'si',
 '围': 'wei',
 '图': 'tu',
 '圆': 'yuan',
 '在': 'zai',
 '场': 'chang',
 '均': 'jun',
 '坐': 'zuo',
 '块': 'kuai',
 '坦': 'tan',
 '型': 'xing',
 '域': 'yu',
 '塞': 'sai',
 '填': 'tian',
 '境': 'jing',
 '墙': 'qiang',
 '壳': 'ke',
 '处': 'chu',
 '复': 'fu',
 '大': 'da',
 '天': 'tian',
 '头': 'tou',
 '夹': 'jia',
 '奇': 'qi',
 '始': 'shi',
 '子': 'zi',
 '字': 'zi',
 '存': 'cun',
 '孤': 'gu',
 '定': 'ding',
 '实': 'shi',
 '宽': 'kuan',
 '密': 'mi',
 '对': 'dui',
 '导': 'dao',
 '射': 'she',
 '小': 'xiao',
 '尔': 'er',
 '尖': 'jian',
 '层': 'ceng',
 '屏': 'ping',
 '展': 'zhan',
 '属': 'shu',
 '岛': 'dao',
 '工': 'gong',
 '差': 'cha',
 '已': 'yi',
 '布': 'bu',
 '希': 'xi',
 '帧': 'zhen',
 '幕': 'mu',
 '平': 'ping',
 '年': 'nian',
 '并': 'bing',
 '幻': 'huan',
 '序': 'xu',
 '库': 'ku',
 '底': 'di',
 '度': 'du',
 '开': 'kai',
 '异': 'yi',
 '式': 'shi',
 '引': 'yin',
 '弦': 'xian',
 '弧': 'hu',
 '形': 'xing',
 '彩': 'cai',
 '影': 'ying',
 '径': 'jing',
 '循': 'xun',
 '快': 'kuai',
 '性': 'xing',
 '息': 'xi',
 '感': 'gan',
 '成': 'cheng',
 '或': 'huo',
 '截': 'jie',
 '户': 'hu',
 '所': 'suo',
 '扑': 'pu',
 '找': 'zhao',
 '投': 'tou',
 '抗': 'kang',
 '折': 'zhe',
 '抠': 'kou',
 '拆': 'chai',
 '拉': 'la',
 '拐': 'guai',
 '拓': 'ta',
 '择': 'ze',
 '拼': 'pin',
 '指': 'zhi',
 '按': 'an',
 '挤': 'ji',
 '捆': 'kun',
 '捉': 'zhuo',
 '捕': 'bu',
 '换': 'huan',
 '据': 'ju',
 '捷': 'jie',
 '排': 'pai',
 '接': 'jie',
 '控': 'kong',
 '描': 'miao',
 '插': 'cha',
 '搜': 'sou',
 '摄': 'she',
 '操': 'cao',
 '收': 'shou',
 '放': 'fang',
 '效': 'xiao',
 '散': 'san',
 '数': 'shu',
 '整': 'zheng',
 '文': 'wen',
 '斑': 'ban',
 '斜': 'xie',
 '断': 'duan',
 '斯': 'si',
 '方': 'fang',
 '旋': 'xuan',
 '旧': 'jiu',
 '时': 'shi',
 '明': 'ming',
 '星': 'xing',
 '映': 'ying',
 '是': 'shi',
 '显': 'xian',
 '普': 'pu',
 '景': 'jing',
 '暗': 'an',
 '曝': 'pu',
 '曲': 'qu',
 '替': 'ti',
 '最': 'zui',
 '朝': 'chao',
 '期': 'qi',
 '木': 'mu',
 '本': 'ben',
 '机': 'ji',
 '权': 'quan',
 '材': 'cai',
 '束': 'shu',
 '条': 'tiao',
 '板': 'ban',
 '极': 'ji',
 '果': 'guo',
 '柄': 'bing',
 '染': 'ran',
 '柔': 'rou',
 '查': 'cha',
 '柱': 'zhu',
 '栅': 'zha',
 '标': 'biao',
 '校': 'xiao',
 '样': 'yang',
 '根': 'gen',
 '格': 'ge',
 '框': 'kuang',
 '桑': 'sang',
 '梯': 'ti',
 '棋': 'qi',
 '棱': 'leng',
 '椭': 'tuo',
 '模': 'mo',
 '次': 'ci',
 '欢': 'huan',
 '欧': 'ou',
 '正': 'zheng',
 '殊': 'shu',
 '段': 'duan',
 '每': 'mei',
 '比': 'bi',
 '毛': 'mao',
 '氏': 'shi',
 '沃': 'wo',
 '沿': 'yan',
 '法': 'fa',
 '波': 'bo',
 '泽': 'ze',
 '活': 'huo',
 '流': 'liu',
 '测': 'ce',
 '浪': 'lang',
 '浮': 'fu',
 '涅': 'nie',
 '淡': 'dan',
 '深': 'shen',
 '混': 'hun',
 '渐': 'jian',
 '温': 'wen',
 '渲': 'xuan',
 '游': 'you',
 '溢': 'yi',
 '滑': 'hua',
 '滤': 'lu',
 '漫': 'man',
 '火': 'huo',
 '灯': 'deng',
 '点': 'dian',
 '烘': 'hong',
 '焙': 'bei',
 '焦': 'jiao',
 '焰': 'yan',
 '片': 'pian',
 '版': 'ban',
 '物': 'wu',
 '特': 'te',
 '率': 'lu',
 '玛': 'ma',
 '环': 'huan',
 '现': 'xian',
 '玻': 'bo',
 '球': 'qiu',
 '理': 'li',
 '瑕': 'xia',
 '璃': 'li',
 '生': 'sheng',
 '用': 'yong',
 '画': 'hua',
 '界': 'jie',
 '畸': 'ji',
 '疵': 'ci',
 '白': 'bai',
 '的': 'de',
 '盘': 'pan',
 '目': 'mu',
 '直': 'zhi',
 '相': 'xiang',
 '真': 'zhen',
 '着': 'zhe',
 '矢': 'shi',
 '矩': 'ju',
 '短': 'duan',
 '石': 'shi',
 '砖': 'zhuan',
 '示': 'shi',
 '离': 'li',
 '秒': 'miao',
 '积': 'ji',
 '称': 'cheng',
 '移': 'yi',
 '程': 'cheng',
 '稳': 'wen',
 '空': 'kong',
 '窗': 'chuang',
 '立': 'li',
 '端': 'duan',
 '笔': 'bi',
 '符': 'fu',
 '等': 'deng',
 '简': 'jian',
 '算': 'suan',
 '类': 'lei',
 '粒': 'li',
 '精': 'jing',
 '糊': 'hu',
 '系': 'xi',
 '素': 'su',
 '索': 'suo',
 '累': 'lei',
 '絮': 'xu',
 '约': 'yue',
 '级': 'ji',
 '纬': 'wei',
 '纹': 'wen',
 '线': 'xian',
 '组': 'zu',
 '细': 'xi',
 '经': 'jing',
 '结': 'jie',
 '绝': 'jue',
 '统': 'tong',
 '维': 'wei',
 '编': 'bian',
 '缘': 'yuan',
 '缩': 'suo',
 '网': 'wang',
 '罗': 'luo',
 '罩': 'zhao',
 '置': 'zhi',
 '翻': 'fan',
 '胀': 'zhang',
 '背': 'bei',
 '能': 'neng',
 '脚': 'jiao',
 '腐': 'fu',
 '膨': 'peng',
 '自': 'zi',
 '至': 'zhi',
 '舍': 'she',
 '色': 'se',
 '节': 'jie',
 '范': 'fan',
 '获': 'huo',
 '菜': 'cai',
 '菲': 'fei',
 '蔽': 'bi',
 '蕴': 'yun',
 '藏': 'cang',
 '蚀': 'shi',
 '蜡': 'la',
 '螺': 'luo',
 '行': 'xing',
 '衡': 'heng',
 '表': 'biao',
 '衰': 'shuai',
 '裁': 'cai',
 '规': 'gui',
 '视': 'shi',
 '览': 'lan',
 '角': 'jiao',
 '解': 'jie',
 '警': 'jing',
 '计': 'ji',
 '设': 'she',
 '评': 'ping',
 '试': 'shi',
 '误': 'wu',
 '说': 'shuo',
 '诺': 'nuo',
 '调': 'diao',
 '贝': 'bei',
 '负': 'fu',
 '质': 'zhi',
 '贴': 'tie',
 '资': 'zi',
 '距': 'ju',
 '路': 'lu',
 '踪': 'zong',
 '身': 'shen',
 '转': 'zhuan',
 '轴': 'zhou',
 '较': 'jiao',
 '辑': 'ji',
 '输': 'shu',
 '边': 'bian',
 '运': 'yun',
 '近': 'jin',
 '述': 'shu',
 '迷': 'mi',
 '追': 'zhui',
 '送': 'song',
 '逆': 'ni',
 '选': 'xuan',
 '透': 'tou',
 '通': 'tong',
 '速': 'su',
 '道': 'dao',
 '遮': 'zhe',
 '邻': 'lin',
 '配': 'pei',
 '采': 'cai',
 '重': 'zhong',
 '量': 'liang',
 '金': 'jin',
 '钳': 'qian',
 '铺': 'pu',
 '锐': 'rui',
 '错': 'cuo',
 '锥': 'zhui',
 '锯': 'ju',
 '镜': 'jing',
 '长': 'zhang',
 '门': 'men',
 '闭': 'bi',
 '间': 'jian',
 '阴': 'yin',
 '阵': 'zhen',
 '阻': 'zu',
 '附': 'fu',
 '降': 'jiang',
 '除': 'chu',
 '随': 'sui',
 '隔': 'ge',
 '集': 'ji',
 '非': 'fei',
 '面': 'mian',
 '顶': 'ding',
 '项': 'xiang',
 '预': 'yu',
 '颜': 'yan',
 '饱': 'bao',
 '马': 'ma',
 '骨': 'gu',
 '骼': 'ge',
 '高': 'gao',
 '黑': 'hei',
 '鼠': 'shu',
 '齐': 'qi',
 '齿': 'chi',
 '龄': 'ling'}


def _init_pinyin_transform() -> bool:
    global PINYIN_TRANSFORM_READY, PINYIN_CF, PINYIN_MANDARIN_LATIN, PINYIN_STRIP_MARKS
    if PINYIN_TRANSFORM_READY is not None:
        return PINYIN_TRANSFORM_READY
    PINYIN_TRANSFORM_READY = False
    if sys.platform != "darwin":
        return False
    path = ctypes.util.find_library("CoreFoundation")
    if not path:
        return False
    try:
        cf = ctypes.CDLL(path)
        cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
        cf.CFStringCreateWithCString.restype = ctypes.c_void_p
        cf.CFStringCreateMutableCopy.argtypes = [ctypes.c_void_p, ctypes.c_long, ctypes.c_void_p]
        cf.CFStringCreateMutableCopy.restype = ctypes.c_void_p
        cf.CFStringTransform.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool]
        cf.CFStringTransform.restype = ctypes.c_bool
        cf.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]
        cf.CFStringGetCString.restype = ctypes.c_bool
        cf.CFRelease.argtypes = [ctypes.c_void_p]
        cf.CFRelease.restype = None
        PINYIN_MANDARIN_LATIN = ctypes.c_void_p.in_dll(cf, "kCFStringTransformMandarinLatin")
        PINYIN_STRIP_MARKS = ctypes.c_void_p.in_dll(cf, "kCFStringTransformStripCombiningMarks")
    except Exception:
        return False
    PINYIN_CF = cf
    PINYIN_TRANSFORM_READY = True
    return True


def _system_pinyin(text: str) -> str:
    if not text or not _init_pinyin_transform():
        return ""
    source = mutable = None
    try:
        source = PINYIN_CF.CFStringCreateWithCString(None, text.encode("utf-8"), 0x08000100)
        if not source:
            return ""
        mutable = PINYIN_CF.CFStringCreateMutableCopy(None, 0, source)
        if not mutable:
            return ""
        if not PINYIN_CF.CFStringTransform(mutable, None, PINYIN_MANDARIN_LATIN, False):
            return ""
        PINYIN_CF.CFStringTransform(mutable, None, PINYIN_STRIP_MARKS, False)
        buffer = ctypes.create_string_buffer(max(1024, len(text.encode("utf-8")) * 12 + 64))
        if not PINYIN_CF.CFStringGetCString(mutable, buffer, len(buffer), 0x08000100):
            return ""
        return buffer.value.decode("utf-8", "ignore")
    except Exception:
        return ""
    finally:
        if mutable:
            PINYIN_CF.CFRelease(mutable)
        if source:
            PINYIN_CF.CFRelease(source)


def _fallback_pinyin(text: str) -> str:
    parts = []
    for char in text:
        pinyin = PINYIN_CHAR_TABLE.get(char)
        if pinyin:
            parts.append(pinyin)
        elif char.isascii() and char.isalnum():
            parts.append(char.lower())
        elif parts and parts[-1] != " ":
            parts.append(" ")
    return " ".join(part for part in parts if part and part != " ")


def _pinyin_search_text(text: str) -> str:
    if not text or not re.search(r"[\u4e00-\u9fff]", text):
        return ""
    cached = PINYIN_TEXT_CACHE.get(text)
    if cached is not None:
        return cached
    raw = _normalize(_system_pinyin(text) or _fallback_pinyin(text))
    if not raw:
        PINYIN_TEXT_CACHE[text] = ""
        return ""
    syllables = raw.split()
    compact = "".join(syllables)
    initials = "".join(part[0] for part in syllables if part)
    value = _normalize(" ".join([raw, compact, initials]))
    PINYIN_TEXT_CACHE[text] = value
    return value


def _preferences():
    addon = bpy.context.preferences.addons.get(ADDON_ID)
    return addon.preferences if addon else None


def _settings_path() -> Path:
    try:
        config_dir = bpy.utils.user_resource("CONFIG", path="", create=True)
    except Exception:
        config_dir = str(Path.home())
    return Path(config_dir) / SETTINGS_FILENAME


def _load_settings() -> dict:
    path = _settings_path()
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    return data if isinstance(data, dict) else {}


def _write_settings(data: dict):
    path = _settings_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    except Exception:
        pass


def _save_preference_settings():
    prefs = _preferences()
    if not prefs:
        return

    data = _load_settings()
    data.update(
        {
            "display_mode": prefs.display_mode,
            "chinese_fuzzy_match": prefs.chinese_fuzzy_match,
            "ui_scale": prefs.ui_scale,
            "shortcut_key": prefs.shortcut_key,
            "shortcut_shift": prefs.shortcut_shift,
            "shortcut_ctrl": prefs.shortcut_ctrl,
            "shortcut_alt": prefs.shortcut_alt,
            "shortcut_oskey": prefs.shortcut_oskey,
            "scan_asset_libraries": prefs.scan_asset_libraries,
            "settings_version": 2,
        }
    )
    _write_settings(data)


def _load_preferences_from_settings():
    prefs = _preferences()
    if not prefs:
        return

    data = _load_settings()
    if data.get("settings_version", 1) < 2 and isinstance(data.get("ui_scale"), (int, float)):
        data["ui_scale"] = max(0.5, min(2.0, float(data["ui_scale"]) / 1.7))
        data["settings_version"] = 2
        _write_settings(data)
    for name in ("display_mode", "chinese_fuzzy_match", "ui_scale", "shortcut_key", "shortcut_shift", "shortcut_ctrl", "shortcut_alt", "shortcut_oskey", "scan_asset_libraries"):
        if name in data:
            try:
                setattr(prefs, name, data[name])
            except Exception:
                pass


def _resolution_scale() -> float:
    preferences = getattr(bpy.context, "preferences", None)
    view = getattr(preferences, "view", None) if preferences else None
    value = getattr(view, "ui_scale", None)
    if isinstance(value, (int, float)) and value > 0:
        return float(value)
    return 1.0


def _ui_scale() -> float:
    prefs = _preferences()
    addon_scale = max(0.5, min(2.0, prefs.ui_scale)) if prefs else 1.0
    return addon_scale * 1.7 * _resolution_scale()


def _scaled(value: float, scale: float) -> float:
    return round(value * scale)


def _load_string_list(name: str) -> list[str]:
    raw = _load_settings().get(name, [])
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, str)]


def _save_string_list(name: str, values: list[str]):
    data = _load_settings()
    data[name] = values
    _write_settings(data)


def _load_favorites() -> set[str]:
    return set(_load_string_list("favorites"))


def _load_shortcuts() -> list[str]:
    seen = set()
    shortcuts = []
    for identifier in _load_string_list("shortcuts"):
        if identifier not in seen:
            shortcuts.append(identifier)
            seen.add(identifier)
    return shortcuts


def _load_favorite_meta() -> dict[str, str]:
    raw = _load_settings().get("favorite_meta", {})
    if not isinstance(raw, dict):
        return {}
    return {key: value for key, value in raw.items() if isinstance(key, str) and isinstance(value, str)}


def _load_asset_index() -> list[dict]:
    raw = _load_settings().get("asset_index", [])
    if not isinstance(raw, list):
        return []

    entries = []
    seen = set()
    for item in raw:
        if isinstance(item, dict):
            blend_path = item.get("path")
            name = item.get("name")
            category = item.get("category", "Asset")
            color_tag = item.get("color_tag", "")
            description = item.get("description", "")
            tree_type = item.get("tree_type", "")
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            blend_path, name = item[:2]
            category = "Asset"
            color_tag = ""
            description = ""
            tree_type = ""
        else:
            continue
        if not isinstance(blend_path, str) or not isinstance(name, str):
            continue
        key = (blend_path, name)
        if key in seen:
            continue
        seen.add(key)
        entries.append({
            "path": blend_path,
            "name": name,
            "category": category if isinstance(category, str) and category else "Asset",
            "color_tag": color_tag if isinstance(color_tag, str) else "",
            "description": description if isinstance(description, str) else "",
            "tree_type": tree_type if isinstance(tree_type, str) else "",
        })
    return entries


def _save_asset_index(entries: list[dict]):
    data = _load_settings()
    data["asset_index"] = entries
    _write_settings(data)


def _node_tree_id(context) -> str:
    tree = getattr(getattr(context, "space_data", None), "edit_tree", None)
    return getattr(tree, "bl_idname", "") or "NodeTree"


def _asset_index_signature() -> str:
    prefs = _preferences()
    if prefs and not prefs.scan_asset_libraries:
        return "assets-disabled"
    payload = json.dumps(_load_asset_index(), ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def _addon_version_string() -> str:
    version = globals().get("ADDON_VERSION")
    if isinstance(version, str) and version:
        return version
    info = globals().get("bl_info", {})
    value = info.get("version", ()) if isinstance(info, dict) else ()
    if value:
        return ".".join(str(part) for part in value)
    return "0.0.0"


def _search_index_cache_key(context) -> str:
    blender = ".".join(str(part) for part in bpy.app.version)
    return f"{_addon_version_string()}:{blender}:{_node_tree_id(context)}:{_asset_index_signature()}"


def _entry_to_cache(entry: NodeSearchEntry) -> dict:
    return {
        "identifier": entry.identifier,
        "category": entry.category,
        "english": entry.english,
        "chinese": entry.chinese,
        "description": entry.description,
        "kind": entry.kind,
        "node_type": entry.node_type,
        "asset_path": entry.asset_path,
        "asset_name": entry.asset_name,
        "asset_color_tag": entry.asset_color_tag,
        "settings": [list(item) for item in entry.settings],
    }


def _entry_from_cache(item: dict) -> NodeSearchEntry | None:
    try:
        english = str(item["english"])
        chinese = str(item.get("chinese") or english)
        node_type = str(item.get("node_type", ""))
        settings = tuple(tuple(pair) for pair in item.get("settings", []))
        label = _entry_label(english, chinese)
        return NodeSearchEntry(
            identifier=str(item["identifier"]),
            category=str(item.get("category", "Node")),
            english=english,
            chinese=chinese,
            label=label,
            description=str(item.get("description", english)),
            kind=str(item.get("kind", "NODE")),
            node_type=node_type,
            asset_path=str(item.get("asset_path", "")),
            asset_name=str(item.get("asset_name", "")),
            asset_color_tag=str(item.get("asset_color_tag", "")),
            search_text=_make_search_text(english, chinese, label, node_type),
            settings=settings,
        )
    except Exception:
        return None


def _load_search_index_cache(context) -> list[NodeSearchEntry] | None:
    cache_key = _search_index_cache_key(context)
    cache = _load_settings().get("search_index_cache", {})
    if not isinstance(cache, dict):
        return None
    raw_entries = cache.get(cache_key)
    if not isinstance(raw_entries, list):
        return None

    entries = []
    for item in raw_entries:
        if isinstance(item, dict):
            entry = _entry_from_cache(item)
            if entry:
                entries.append(entry)
    if entries:
        SEARCH_INDEX_MEMORY_KEYS.add(cache_key)
    return entries or None


def _load_bundled_search_index(context) -> list[NodeSearchEntry] | None:
    cache_path = Path(__file__).with_name(BUNDLED_CACHE_FILENAME)
    if not cache_path.exists():
        return None

    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    trees = payload.get("trees") if isinstance(payload, dict) else None
    if not isinstance(trees, dict):
        return None

    raw_entries = trees.get(_node_tree_id(context))
    if not isinstance(raw_entries, list):
        return None

    entries = []
    for item in raw_entries:
        if isinstance(item, dict):
            entry = _entry_from_cache(item)
            if entry:
                entries.append(entry)
    return entries or None


def _save_search_index_cache(context, entries: list[NodeSearchEntry]):
    cache_key = _search_index_cache_key(context)
    if cache_key in SEARCH_INDEX_MEMORY_KEYS:
        return

    data = _load_settings()
    cache = data.get("search_index_cache", {})
    if not isinstance(cache, dict):
        cache = {}
    cache[cache_key] = [_entry_to_cache(entry) for entry in entries]
    if len(cache) > 12:
        for key in list(cache.keys())[:-12]:
            cache.pop(key, None)
    data["search_index_cache"] = cache
    _write_settings(data)
    SEARCH_INDEX_MEMORY_KEYS.add(cache_key)


def _save_favorites(favorites: set[str], favorite_meta: dict[str, str] | None = None):
    data = _load_settings()
    data["favorites"] = sorted(favorites)
    if favorite_meta is not None:
        data["favorite_meta"] = {key: favorite_meta[key] for key in sorted(favorite_meta)}
    _write_settings(data)


def _save_shortcuts(shortcuts: list[str]):
    _save_string_list("shortcuts", shortcuts)


def _add_shortcut(identifier: str):
    shortcuts = _load_shortcuts()
    if identifier not in shortcuts:
        shortcuts.append(identifier)
        _save_shortcuts(shortcuts)


def _remove_shortcut(identifier: str):
    _save_shortcuts([item for item in _load_shortcuts() if item != identifier])


def _move_shortcut(identifier: str, delta: int):
    shortcuts = _load_shortcuts()
    if identifier not in shortcuts:
        return
    index = shortcuts.index(identifier)
    new_index = max(0, min(len(shortcuts) - 1, index + delta))
    if new_index == index:
        return
    shortcuts.insert(new_index, shortcuts.pop(index))
    _save_shortcuts(shortcuts)


def _remove_favorite(identifier: str):
    favorites = _load_favorites()
    favorite_meta = _load_favorite_meta()
    favorites.discard(identifier)
    favorite_meta.pop(identifier, None)
    _save_favorites(favorites, favorite_meta)


def _preference_changed(_self, _context):
    _clear_search_caches()
    _save_preference_settings()


def _shortcut_changed(_self, _context):
    _save_preference_settings()
    refresh_keymap()


def _translation_label(text: str, translation_context: str | None = None) -> str:
    if not text:
        return text

    cache_key = (text, translation_context)
    cached = TRANSLATION_LABEL_CACHE.get(cache_key)
    if cached is not None:
        return cached

    view = bpy.context.preferences.view
    original_language = view.language
    original_iface = view.use_translate_interface
    original_data = view.use_translate_new_dataname
    translated = text

    try:
        view.language = "zh_HANS"
        view.use_translate_interface = True
        view.use_translate_new_dataname = True
        for translate in (
            getattr(bpy.app.translations, "pgettext_iface", None),
            getattr(bpy.app.translations, "pgettext_data", None),
        ):
            if not translate:
                continue

            try:
                candidate = translate(text, translation_context) if translation_context else translate(text)
            except Exception:
                continue

            if candidate and candidate != text:
                translated = candidate
                break
    finally:
        try:
            view.language = original_language
            view.use_translate_interface = original_iface
            view.use_translate_new_dataname = original_data
        except Exception:
            pass

    TRANSLATION_LABEL_CACHE[cache_key] = translated
    return translated


def _display_mode() -> str:
    prefs = _preferences()
    return prefs.display_mode if prefs else "ENGLISH_CHINESE"


def _chinese_fuzzy_match_enabled() -> bool:
    prefs = _preferences()
    return bool(prefs and prefs.chinese_fuzzy_match)


def _entry_label(english: str, chinese: str) -> str:
    display_mode = _display_mode()

    if display_mode == "ENGLISH":
        return english
    if display_mode == "CHINESE" and chinese != english:
        return chinese
    if display_mode == "CHINESE_ENGLISH" and chinese != english:
        return f"{chinese} / {english}"
    if chinese != english:
        return f"{english} / {chinese}"

    return english


def _entry_primary_label(entry: NodeSearchEntry) -> str:
    display_mode = _display_mode()
    if display_mode in {"CHINESE", "CHINESE_ENGLISH"} and entry.chinese != entry.english:
        return entry.chinese
    return entry.english


def _entry_display_label(identifier: str, fallback: str = "") -> str:
    entry = NODE_ENTRY_BY_ID.get(identifier)
    return entry.label if entry else fallback or identifier


def _settings_dict(settings: tuple[tuple[str, str], ...]) -> dict[str, str]:
    return {str(name): str(value) for name, value in settings}


def _append_category_parts(category: str, parts: list[str]) -> str:
    result = category
    existing = [part.strip() for part in category.split(" > ") if part.strip()]
    for part in parts:
        if not part:
            continue
        if existing and existing[-1] == part:
            continue
        result = f"{result} > {part}" if result else part
        existing.append(part)
    return result


def _display_parts(entry: NodeSearchEntry) -> tuple[str, str]:
    category = entry.category
    english_parts = [part.strip() for part in entry.english.split(" > ") if part.strip()]
    chinese_parts = [part.strip() for part in entry.chinese.split(" > ") if part.strip()]

    if len(english_parts) <= 1:
        return category, _entry_label(entry.english, entry.chinese)

    settings = _settings_dict(entry.settings)
    category_parts = english_parts[:-1]
    chinese_label = chinese_parts[-1] if len(chinese_parts) == len(english_parts) else ""

    if entry.node_type == "ShaderNodeMix" and settings.get("data_type") == "RGBA" and "blend_type" in settings:
        category_parts = ["Mix Color"]
    elif entry.node_type == "ShaderNodeMix" and settings.get("data_type") == "RGBA" and entry.english == "Mix > Mix Color":
        return category, _entry_label("Mix Color", chinese_parts[-1] if chinese_parts else entry.chinese)
    elif entry.node_type == "ShaderNodeMix" and settings.get("data_type") in {"VECTOR", "ROTATION"}:
        category_parts = []

    category = _append_category_parts(category, category_parts)
    english = english_parts[-1]
    chinese = chinese_label or english
    return category, _entry_label(english, chinese)


def _blend_color(color: tuple[float, float, float, float], amount: float, target: tuple[float, float, float, float] = PANEL_BACKGROUND) -> tuple[float, float, float, float]:
    amount = max(0.0, min(1.0, amount))
    return (
        color[0] * amount + target[0] * (1.0 - amount),
        color[1] * amount + target[1] * (1.0 - amount),
        color[2] * amount + target[2] * (1.0 - amount),
        color[3],
    )


def _entry_base_type_color(entry: NodeSearchEntry) -> tuple[float, float, float, float]:
    category_parts = [_normalize(part) for part in entry.category.split(" > ") if part.strip()]
    english_parts = [_normalize(part) for part in entry.english.split(" > ") if part.strip()]
    node_type_words = _camel_words(entry.node_type or "").split()
    keys = category_parts + english_parts + node_type_words
    first_category = category_parts[0] if category_parts else ""

    if entry.node_type == "NodeGroupInput":
        return NODE_TYPE_COLORS["output"]
    if entry.asset_color_tag:
        tag_type = NODE_COLOR_TAG_TYPES.get(entry.asset_color_tag.upper())
        if tag_type:
            return NODE_TYPE_COLORS[tag_type]
    if entry.node_type == "NodeGroupOutput":
        return NODE_TYPE_COLORS["output"]
    normalized_english = _normalize(entry.english or "")
    if entry.node_type == "NodeEvaluateClosure" or normalized_english == "evaluate closure":
        return NODE_TYPE_COLORS["converter"]
    if normalized_english == "closure" or entry.node_type in {"NodeClosureInput", "NodeClosureOutput"}:
        return NODE_TYPE_COLORS["none"]
    if normalized_english == "smooth by angle" or normalized_english == "get geometry bundle":
        return NODE_TYPE_COLORS["geometry"]
    if normalized_english == "separate color":
        return NODE_TYPE_COLORS["color"]
    if entry.node_type in {"GeometryNodeSetGreasePencilColor", "GeometryNodeSetGreasePencilDepth", "GeometryNodeSetGreasePencilSoftness"}:
        return NODE_TYPE_COLORS["geometry"]
    if normalized_english in {"instance rotation", "uv tangent", "special characters"}:
        return NODE_TYPE_COLORS["input"]
    if normalized_english in {"pack uv islands", "uv unwrap", "index of nearest"}:
        return NODE_TYPE_COLORS["converter"]
    if normalized_english == "radial tiling":
        return NODE_TYPE_COLORS["vector"]
    if entry.node_type in {"ShaderNodeVectorRotate", "ShaderNodeVectorMath", "ShaderNodeVectorCurve"}:
        return NODE_TYPE_COLORS["vector"]
    settings = dict(entry.settings)
    if entry.node_type == "ShaderNodeMix" and (settings.get("data_type") == "VECTOR" or "mix vector" in normalized_english):
        return NODE_TYPE_COLORS["vector"]
    if entry.node_type in {"FunctionNodeAlignEulerToVector", "FunctionNodeRotateVector", "FunctionNodeRotateRotation"}:
        return NODE_TYPE_COLORS["converter"]
    if "read" in category_parts:
        return NODE_TYPE_COLORS["input"]
    if first_category in {"attribute", "input", "color", "output", "texture", "geometry", "vector"}:
        return NODE_TYPE_COLORS[first_category]
    if first_category in GEOMETRY_COLOR_KEYS or any(key in GEOMETRY_COLOR_KEYS for key in category_parts[:1]):
        return NODE_TYPE_COLORS["geometry"]
    if first_category in VECTOR_COLOR_KEYS or any(key in VECTOR_COLOR_KEYS for key in category_parts[:1]):
        return NODE_TYPE_COLORS["vector"]
    if first_category in CONVERTER_COLOR_KEYS or any(key in CONVERTER_COLOR_KEYS for key in keys):
        return NODE_TYPE_COLORS["converter"]
    if entry.kind == "ASSET":
        return NODE_TYPE_COLORS["none"]
    return CATEGORY_COLOR_FALLBACK


def _entry_type_colors(entry: NodeSearchEntry, active: bool = False) -> tuple[tuple[float, float, float, float], tuple[float, float, float, float]]:
    base = _entry_base_type_color(entry)
    fill_strength = 0.58 if active else 0.16
    border_strength = 0.74 if active else 0.50
    fill_alpha = 0.92 if active else 0.64
    border_alpha = 0.92 if active else 0.82
    fill = _blend_color(base, fill_strength)
    border = _blend_color(base, border_strength)
    return (fill[0], fill[1], fill[2], fill_alpha), (border[0], border[1], border[2], border_alpha)


def _entry_display_depth(entry: NodeSearchEntry) -> int:
    category_depth = len([part for part in entry.category.split(" > ") if part.strip()])
    english_depth = len([part for part in entry.english.split(" > ") if part.strip()])
    return category_depth + max(1, english_depth)


def _token_matches_word_prefix(token: str, word: str) -> bool:
    if not token or not word:
        return False
    if word.startswith(token):
        return True
    if len(token) < 4 or word[0] != token[0]:
        return False

    position = 0
    skipped = 0
    for char in token:
        found = word.find(char, position)
        if found < 0:
            return False
        skipped += max(0, found - position)
        position = found + 1
    return skipped <= max(1, len(token) // 3)


def _word_prefix_tokens_match(text: str, tokens: list[str]) -> bool:
    if not tokens:
        return False
    words = _normalize(text).split()
    if not words:
        return False
    return all(any(_token_matches_word_prefix(token, word) for word in words) for token in tokens)


def _ordered_chars_match(needle: str, haystack: str) -> bool:
    needle = _compact(needle)
    haystack = _compact(haystack)
    if len(needle) < 4 or not haystack:
        return False
    position = 0
    skipped = 0
    for char in needle:
        found = haystack.find(char, position)
        if found < 0:
            return False
        skipped += max(0, found - position)
        position = found + 1
    return skipped <= max(4, len(needle) * 2)


def _path_without_leaf(entry: NodeSearchEntry) -> str:
    english_parts = [part.strip() for part in entry.english.split(" > ") if part.strip()]
    if len(english_parts) > 1:
        return " > ".join(english_parts[:-1])
    return entry.english


def _query_match_parts(entry: NodeSearchEntry, query: str):
    query = _normalize(query)
    tokens = query.split()
    english = _normalize(entry.english)
    chinese = _normalize(entry.chinese)
    english_parts = [_normalize(part) for part in entry.english.split(" > ") if part.strip()]
    chinese_parts = [_normalize(part) for part in entry.chinese.split(" > ") if part.strip()]
    category_parts = [_normalize(part) for part in entry.category.split(" > ") if part.strip()]
    category_text = _normalize(entry.category)
    leaf_parts = [parts[-1] for parts in (english_parts, chinese_parts) if parts]
    root_parts = [parts[0] for parts in (english_parts, chinese_parts) if len(parts) > 1]
    category_match = bool(query and (
        query in category_parts
        or any(part.startswith(query) for part in category_parts)
        or (tokens and all(token in category_text for token in tokens))
    ))
    leaf_exact = any(part == query for part in leaf_parts)
    leaf_prefix = any(part.startswith(query) for part in leaf_parts)
    leaf_contains = any(query in part for part in leaf_parts)
    root_exact = any(part == query for part in root_parts)
    path_text = " ".join([entry.category, entry.english])
    leaf_word_match = any(_word_prefix_tokens_match(part, tokens) for part in leaf_parts)
    path_word_match = _word_prefix_tokens_match(path_text, tokens)
    root_word_match = _word_prefix_tokens_match(_path_without_leaf(entry), tokens)
    if _chinese_fuzzy_match_enabled():
        chinese_search_text = _make_chinese_search_text(entry.chinese, entry.label)
        ordered_leaf_match = any(_ordered_chars_match(query, part) for part in chinese_parts[-1:])
        ordered_search_match = _ordered_chars_match(query, chinese_search_text)
    else:
        ordered_leaf_match = False
        ordered_search_match = False
    is_primary = len(english_parts) <= 1
    return {
        "english": english,
        "chinese": chinese,
        "english_parts": english_parts,
        "chinese_parts": chinese_parts,
        "category_parts": category_parts,
        "leaf_parts": leaf_parts,
        "root_parts": root_parts,
        "category_match": category_match,
        "leaf_exact": leaf_exact,
        "leaf_prefix": leaf_prefix,
        "leaf_contains": leaf_contains,
        "leaf_word_match": leaf_word_match,
        "path_word_match": path_word_match,
        "root_word_match": root_word_match,
        "ordered_leaf_match": ordered_leaf_match,
        "ordered_search_match": ordered_search_match,
        "root_exact": root_exact,
        "is_primary": is_primary,
    }


OFFICIALISH_QUERY_ORDER = {
    "math": (
        "math",
        "vector math",
        "boolean math",
        "integer math",
        "bit math",
        "bit math > and",
        "bit math > exclusive or",
        "bit math > not",
        "bit math > or",
        "bit math > rotate",
    ),
    "vector": (
        "vector",
        "mix vector",
        "vector math",
        "vector curves",
        "vector rotate",
        "rotate vector",
        "align rotation to vector",
        "combine cylindrical",
        "combine spherical",
        "combine xyz",
        "separate xyz",
    ),
    "mesh": (
        "dual mesh",
        "mesh line",
        "mesh island",
        "mesh circle",
        "grid to mesh",
        "extrude mesh",
        "mesh boolean",
        "mesh to curve",
        "curve to mesh",
        "mesh to points",
    ),
    "curve": (
        "curve tip",
        "rgb curves",
        "curve root",
        "curve info",
        "curve tilt",
        "fill curve",
        "trim curve",
        "curve line",
        "float curve",
        "curve to tube",
    ),
    "geometry": (
        "join geometry",
        "transform geometry",
        "geometry input",
        "delete geometry",
        "smooth geometry",
        "set geometry name",
        "displace geometry",
        "separate geometry",
        "geometry proximity",
        "geometry to instance",
    ),
    "position": (
        "position",
        "set position",
        "set handle positions",
        "curve handle positions",
        "projection matrix",
    ),
    "color": (
        "color",
        "mix color > color",
        "object info > color",
        "volume info > color",
        "mix color",
        "color ramp",
        "color burn",
        "color dodge",
        "invert color",
        "combine color",
    ),
    "obj": (
        "texture coordinate > object",
        "object info",
        "object info > object index",
        "object info > alpha",
        "object info > color",
        "object info > location",
        "object info > material index",
        "object info > random",
        "combine color",
        "combine bundle",
    ),
    "object": (
        "texture coordinate > object",
        "object info",
        "object info > object index",
        "object info > alpha",
        "object info > color",
        "object info > location",
        "object info > material index",
        "object info > random",
        "combine color",
        "combine bundle",
    ),
    "node": (
        "noise texture",
        "hair curves noise",
        "white noise texture",
    ),
}


def _has_visible_output_setting(entry: NodeSearchEntry) -> bool:
    return any(name == "visible_output" for name, _value in entry.settings)


def _dynamic_preferred_order(entry: NodeSearchEntry, query: str) -> int:
    match = _query_match_parts(entry, query)
    if match["leaf_exact"]:
        return 1_000
    if match["is_primary"] and match["leaf_word_match"]:
        return 1_050
    if _has_visible_output_setting(entry) and match["root_word_match"]:
        return 1_100
    if _has_visible_output_setting(entry) and match["leaf_contains"]:
        return 1_200
    if match["is_primary"] and match["leaf_contains"]:
        return 1_400
    if match["leaf_prefix"]:
        return 1_600
    if match["leaf_contains"]:
        return 1_800
    if match["ordered_leaf_match"]:
        return 2_000
    if match["root_exact"]:
        return 2_200
    if match["path_word_match"]:
        return 2_400
    if match["category_match"]:
        return 3_000
    return 10_000


def _officialish_preferred_order(entry: NodeSearchEntry, query: str) -> int:
    preferred = OFFICIALISH_QUERY_ORDER.get(_normalize(query))
    if not preferred:
        return _dynamic_preferred_order(entry, query)

    english_parts = [_normalize(part) for part in entry.english.split(" > ") if part.strip()]
    if not english_parts:
        return 10_000

    leaf = english_parts[-1]
    full = " > ".join(english_parts)
    for index, name in enumerate(preferred):
        if " > " in name:
            if full == name or full.endswith(f" > {name}"):
                return index
        elif leaf == name or full == name:
            return index
    return _dynamic_preferred_order(entry, query)


def _officialish_sort_bucket(entry: NodeSearchEntry, query: str) -> int:
    match = _query_match_parts(entry, query)
    if match["is_primary"] and match["leaf_exact"]:
        return 0
    if match["is_primary"] and (match["category_match"] or match["leaf_contains"]):
        return 1
    if match["is_primary"]:
        return 2
    if match["root_exact"] or match["category_match"]:
        return 3
    if match["leaf_contains"]:
        return 4
    return 5


def _primary_match_order(entry: NodeSearchEntry, query: str) -> int:
    match = _query_match_parts(entry, query)
    leaf = match["leaf_parts"][0] if match["leaf_parts"] else ""
    category_parts = match["category_parts"]
    in_leaf = query in leaf
    in_category = query in category_parts or any(part.startswith(query) for part in category_parts)
    if match["leaf_exact"]:
        return 0
    if in_category and in_leaf and not leaf.startswith(query):
        return 1
    if in_category and in_leaf:
        return 2
    if in_leaf:
        return 3
    if in_category:
        return 4
    return 5


def _node_tree_allows_node(context, node_type: str) -> bool:
    space = context.space_data
    node_tree = getattr(space, "edit_tree", None)
    if not node_tree:
        return False

    bl_rna = bpy.types.Node.bl_rna_get_subclass(node_type)
    if bl_rna is None:
        return False

    node_cls = getattr(bpy.types, node_type, None)
    if node_cls is None:
        return True

    poll = getattr(node_cls, "poll", None)
    if not poll:
        return True

    try:
        return bool(poll(node_tree))
    except Exception:
        return True


def _iter_node_classes():
    global NODE_CLASS_CACHE

    if NODE_CLASS_CACHE is not None:
        yield from NODE_CLASS_CACHE
        return

    pending = list(bpy.types.Node.__subclasses__())
    seen = set()
    classes = []

    while pending:
        cls = pending.pop()
        if cls in seen:
            continue

        seen.add(cls)
        pending.extend(cls.__subclasses__())

        bl_idname = getattr(cls, "bl_idname", "")
        bl_label = getattr(cls, "bl_label", "")
        if bl_idname and bl_label:
            classes.append(cls)

    NODE_CLASS_CACHE = classes
    yield from classes


def _node_menu_script_paths(context) -> list[Path]:
    menu_files = {
        "GeometryNodeTree": {"node_add_menu.py", "node_add_menu_geometry.py"},
        "ShaderNodeTree": {"node_add_menu.py", "node_add_menu_shader.py"},
        "CompositorNodeTree": {"node_add_menu.py", "node_add_menu_compositor.py"},
        "TextureNodeTree": {"node_add_menu.py", "node_add_menu_texture.py"},
    }
    tree = getattr(getattr(context, "space_data", None), "edit_tree", None)
    allowed_names = menu_files.get(getattr(tree, "bl_idname", ""), {"node_add_menu.py"})
    paths = []

    for resource_type in ("LOCAL", "SYSTEM", "USER"):
        try:
            resource_path = Path(bpy.utils.resource_path(resource_type))
        except Exception:
            continue

        ui_path = resource_path / "scripts/startup/bl_ui"
        if ui_path.exists():
            paths.extend(path for path in sorted(ui_path.glob("node_add_menu*.py")) if path.name in allowed_names)

    return paths


def _constant_string(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _constant_string_list(node) -> list[str]:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return []
    values = []
    for item in node.elts:
        value = _constant_string(item)
        if value:
            values.append(value)
    return values


def _class_string_assignment(class_node: ast.ClassDef, name: str) -> str | None:
    for item in class_node.body:
        if not isinstance(item, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in item.targets):
            continue
        value = _constant_string(item.value)
        if value:
            return value
    return None


def _call_keyword_string(node: ast.Call, name: str) -> str | None:
    for keyword in node.keywords:
        if keyword.arg == name:
            return _constant_string(keyword.value)
    return None


def _shader_mix_label_settings(label: str | None) -> tuple[str, tuple[tuple[str, str], ...]]:
    if label == "Mix Color":
        return label, (("data_type", "RGBA"),)
    if label == "Mix Vector":
        return label, (("data_type", "VECTOR"),)
    if label == "Mix Rotation":
        return label, (("data_type", "ROTATION"),)
    return "", ()


def _category_from_menu_path(menu_path: str | None) -> str | None:
    if not menu_path:
        return None
    parts = [part.strip() for part in menu_path.split("/") if part.strip()]
    return " > ".join(parts) if parts else None


def _category_from_class_name(name: str) -> str:
    if name in {"NodeMenu", "Menu"} or not name.startswith("NODE_MT_"):
        return ""

    text = name
    for prefix in ("NODE_MT_gn_", "NODE_MT_shader_node_", "NODE_MT_compositor_node_", "NODE_MT_texture_node_", "NODE_MT_category_", "NODE_MT_"):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    text = re.sub(r"_base$", "", text)
    tokens = [token for token in text.split("_") if token not in {"node", "nodes", "all", "category"}]
    if not tokens:
        return "Node"

    labels = {
        "gn": "Geometry",
        "uv": "UV",
    }
    return " > ".join(labels.get(token, token.replace("and", "&").title()) for token in tokens)


def _enum_items_for_node_property(node_type: str, property_name: str):
    node_cls = getattr(bpy.types, node_type, None)
    if not node_cls:
        return

    try:
        prop = node_cls.bl_rna.properties[property_name]
    except Exception:
        return

    translation_context = getattr(prop, "translation_context", None)
    for item in prop.enum_items_static:
        english = item.name
        chinese = _translation_label(english, translation_context)
        yield item.identifier, english, chinese


def _iter_menu_entries(context):
    tree_id = getattr(getattr(getattr(context, "space_data", None), "edit_tree", None), "bl_idname", "")
    if tree_id in MENU_ENTRY_CACHE:
        yield from MENU_ENTRY_CACHE[tree_id]
        return

    seen = set()
    entries = []

    def add_entry(node_type, category, variant_label, variant_chinese, settings):
        entries.append((node_type, category, variant_label, variant_chinese, tuple(settings)))

    for path in _node_menu_script_paths(context):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        for class_node in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
            category = _category_from_menu_path(_class_string_assignment(class_node, "menu_path")) or _category_from_class_name(class_node.name)
            if not category:
                continue

            for node in ast.walk(class_node):
                if not isinstance(node, ast.Call):
                    continue

                func = node.func
                if not isinstance(func, ast.Attribute):
                    continue

                if func.attr in {"add_color_mix_node", "color_mix_node"}:
                    key = ("ShaderNodeMix", (), category)
                    if key not in seen:
                        seen.add(key)
                        add_entry("ShaderNodeMix", category, "Mix Color", _translation_label("Mix Color"), (("data_type", "RGBA"),))
                    for item_identifier, item_english, item_chinese in _enum_items_for_node_property("ShaderNodeMix", "blend_type"):
                        settings = (("data_type", "RGBA"), ("blend_type", item_identifier))
                        key = ("ShaderNodeMix", settings, category)
                        if key in seen:
                            continue
                        seen.add(key)
                        add_entry("ShaderNodeMix", category, item_english, item_chinese, settings)
                    continue

                if func.attr not in {"node_operator", "node_operator_with_outputs", "node_operator_with_searchable_enum"}:
                    continue

                candidates = [_constant_string(arg) for arg in node.args]
                node_type = next((candidate for candidate in candidates if candidate and "Node" in candidate), None)
                if not node_type:
                    continue

                variant_label = ""
                base_settings = ()
                if node_type == "ShaderNodeMix" and func.attr == "node_operator":
                    variant_label, base_settings = _shader_mix_label_settings(_call_keyword_string(node, "label"))

                key = (node_type, base_settings, category)
                if key not in seen:
                    seen.add(key)
                    add_entry(node_type, category, variant_label, _translation_label(variant_label) if variant_label else "", base_settings)

                if func.attr == "node_operator_with_outputs":
                    output_names = []
                    for arg in node.args:
                        output_names.extend(_constant_string_list(arg))
                    for output_name in output_names:
                        settings = (("visible_output", output_name),)
                        key = (node_type, settings, category)
                        if key in seen:
                            continue
                        seen.add(key)
                        add_entry(node_type, category, output_name, _translation_label(output_name), settings)
                    continue

                if func.attr != "node_operator_with_searchable_enum":
                    continue

                property_name = next(
                    (
                        candidate
                        for candidate in candidates
                        if candidate and candidate != node_type and "Node" not in candidate
                    ),
                    "",
                )
                if not property_name:
                    continue

                for item_identifier, item_english, item_chinese in _enum_items_for_node_property(node_type, property_name):
                    settings = ((property_name, item_identifier),)
                    key = (node_type, settings, category)
                    if key in seen:
                        continue
                    seen.add(key)
                    add_entry(node_type, category, item_english, item_chinese, settings)

    MENU_ENTRY_CACHE[tree_id] = entries
    yield from entries


def _built_in_asset_node_directories() -> list[Path]:
    directories = []
    for resource_type in ("LOCAL", "SYSTEM", "USER"):
        try:
            resource_path = Path(bpy.utils.resource_path(resource_type))
        except Exception:
            continue

        nodes_dir = resource_path / "datafiles/assets/nodes"
        if nodes_dir.exists():
            directories.append(nodes_dir)
    return directories


def _external_asset_node_directories() -> list[Path]:
    directories = []
    try:
        for library in bpy.context.preferences.filepaths.asset_libraries:
            library_path = Path(bpy.path.abspath(library.path))
            if library_path.exists():
                directories.append(library_path)
    except Exception:
        pass
    return directories


def _asset_category_from_catalog(catalog_name: str, blend_path: Path) -> str:
    if catalog_name.strip().lower() == "instances":
        return "Instance"

    if catalog_name:
        normalized = catalog_name.replace("-", " > ").replace("/", " > ")
        parts = [part.strip() for part in normalized.split(">") if part.strip()]
        if parts:
            return " > ".join(parts)

    stem = blend_path.stem.replace("_nodes_essentials", "").replace("_", " ").strip().title()
    return stem or "Asset"


def _read_asset_node_groups(blend_path: Path) -> list[dict]:
    loaded_groups = []
    try:
        with bpy.data.libraries.load(str(blend_path), assets_only=True) as (data_from, data_to):
            names = list(getattr(data_from, "node_groups", ()))
            data_to.node_groups = names
            loaded_groups = data_to.node_groups
    except TypeError:
        try:
            with bpy.data.libraries.load(str(blend_path)) as (data_from, data_to):
                names = list(getattr(data_from, "node_groups", ()))
                data_to.node_groups = names
                loaded_groups = data_to.node_groups
        except Exception:
            return []
    except Exception:
        return []

    entries = []
    for node_group in loaded_groups:
        if not node_group:
            continue
        asset_data = getattr(node_group, "asset_data", None)
        catalog_name = str(getattr(asset_data, "catalog_simple_name", "") or "") if asset_data else ""
        description = str(getattr(asset_data, "description", "") or "") if asset_data else ""
        color_tag = str(getattr(node_group, "color_tag", "") or "")
        entries.append({
            "path": str(blend_path),
            "name": node_group.name,
            "category": _asset_category_from_catalog(catalog_name, blend_path),
            "color_tag": color_tag,
            "description": description,
            "tree_type": str(getattr(node_group, "bl_idname", "") or ""),
        })

    for node_group in loaded_groups:
        if node_group:
            try:
                bpy.data.node_groups.remove(node_group)
            except Exception:
                pass

    return entries


def _iter_asset_blend_paths(directories: list[Path]):
    for nodes_dir in directories:
        try:
            yield from sorted(nodes_dir.rglob("*.blend"))
        except Exception:
            continue


def _scan_asset_node_groups(directories: list[Path]) -> list[dict]:
    seen = set()
    entries = []

    for blend_path in _iter_asset_blend_paths(directories):
        for item in _read_asset_node_groups(blend_path):
            key = (item["path"], item["name"])
            if key in seen:
                continue
            seen.add(key)
            entries.append(item)

    return entries


def _background_asset_index_step():
    global BACKGROUND_ASSET_INDEX
    state = BACKGROUND_ASSET_INDEX
    if not state:
        return None

    deadline = time.monotonic() + 0.012
    processed = 0
    while time.monotonic() < deadline and processed < 1:
        try:
            blend_path = next(state["paths"])
        except StopIteration:
            _save_asset_index(state["entries"])
            _clear_search_caches()
            BACKGROUND_ASSET_INDEX = None
            return None

        for item in _read_asset_node_groups(blend_path):
            key = (item["path"], item["name"])
            if key in state["seen"]:
                continue
            state["seen"].add(key)
            state["entries"].append(item)
        processed += 1

    return 0.75


def _start_background_asset_index():
    global BACKGROUND_ASSET_INDEX
    prefs = _preferences()
    if prefs and not prefs.scan_asset_libraries:
        return

    directories = _built_in_asset_node_directories() + _external_asset_node_directories()
    if not directories:
        return

    BACKGROUND_ASSET_INDEX = {
        "paths": iter(_iter_asset_blend_paths(directories)),
        "entries": [],
        "seen": set(),
    }
    try:
        bpy.app.timers.register(_background_asset_index_step, first_interval=3.0)
    except Exception:
        pass


def _refresh_asset_index() -> int:
    global BACKGROUND_ASSET_INDEX
    BACKGROUND_ASSET_INDEX = None
    directories = _built_in_asset_node_directories() + _external_asset_node_directories()
    entries = _scan_asset_node_groups(directories)
    _save_asset_index(entries)
    _clear_search_caches()
    return len(entries)


def _iter_asset_node_groups():
    prefs = _preferences()
    if prefs and not prefs.scan_asset_libraries:
        return

    for item in _load_asset_index():
        yield Path(item["path"]), item


def _make_english_search_text(english: str, node_type: str = "") -> str:
    pieces = [
        english,
        english.replace(" ", ""),
        _camel_words(node_type),
    ]
    return _normalize(" ".join(piece for piece in pieces if piece))


def _make_chinese_search_text(chinese: str, label: str) -> str:
    pieces = [
        chinese,
        label,
        chinese.replace(" ", ""),
        _pinyin_search_text(chinese),
        _pinyin_search_text(label),
    ]
    return _normalize(" ".join(piece for piece in pieces if piece))


def _make_search_text(english: str, chinese: str, label: str, node_type: str) -> str:
    pieces = [
        _make_english_search_text(english, node_type),
        _make_chinese_search_text(chinese, label),
    ]
    return _normalize(" ".join(piece for piece in pieces if piece))


def _rebuild_search_entries(context):
    NODE_SEARCH_ENTRIES.clear()
    NODE_ENTRY_BY_ID.clear()

    seen_keys = set()

    def add_entry(entry: NodeSearchEntry):
        NODE_SEARCH_ENTRIES.append(entry)
        NODE_ENTRY_BY_ID[entry.identifier] = entry

    def remember_key(entry: NodeSearchEntry):
        if entry.kind == "NODE":
            seen_keys.add((entry.node_type, tuple(entry.settings)))
        elif entry.kind == "ASSET" and entry.asset_path:
            seen_keys.add(("ASSET", entry.asset_path, entry.asset_name))

    def add_local_groups():
        space = context.space_data
        edit_tree = getattr(space, "edit_tree", None)
        if not edit_tree:
            return

        for node_group in bpy.data.node_groups:
            if node_group == edit_tree or node_group.bl_idname != edit_tree.bl_idname:
                continue
            asset_name = node_group.name
            key = ("LOCAL_GROUP", asset_name)
            name_key = _normalize(asset_name)
            if key in seen_keys or any(_normalize(entry.english) == name_key for entry in NODE_SEARCH_ENTRIES):
                continue
            seen_keys.add(key)
            chinese = _translation_label(asset_name)
            label = _entry_label(asset_name, chinese)
            identifier = _safe_identifier("G", asset_name)
            add_entry(
                NodeSearchEntry(
                    identifier=identifier,
                    category="Group",
                    english=asset_name,
                    chinese=chinese,
                    label=label,
                    description=f"Node group: {asset_name}",
                    kind="ASSET",
                    asset_name=asset_name,
                    search_text=_make_search_text(asset_name, chinese, label, ""),
                )
            )

    def add_asset_library_entries(cacheable_entries: list[NodeSearchEntry] | None = None):
        space = context.space_data
        edit_tree = getattr(space, "edit_tree", None)
        if not edit_tree or edit_tree.bl_idname != "GeometryNodeTree":
            return

        for blend_path, asset_item in _iter_asset_node_groups():
            tree_type = asset_item.get("tree_type", "")
            if tree_type and tree_type != edit_tree.bl_idname:
                continue
            asset_name = asset_item["name"]
            key = ("ASSET", str(blend_path), asset_name)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            chinese = _translation_label(asset_name)
            label = _entry_label(asset_name, chinese)
            description = asset_item.get("description") or f"Node group asset: {asset_name}"
            entry = NodeSearchEntry(
                identifier=_safe_identifier("A", asset_name, str(blend_path)),
                category=asset_item.get("category") or "Asset",
                english=asset_name,
                chinese=chinese,
                label=label,
                description=description,
                kind="ASSET",
                asset_path=str(blend_path),
                asset_name=asset_name,
                asset_color_tag=asset_item.get("color_tag", ""),
                search_text=_make_search_text(asset_name, chinese, label, ""),
            )
            if cacheable_entries is not None:
                cacheable_entries.append(entry)
            add_entry(entry)

    def add_zone_entries():
        space = context.space_data
        edit_tree = getattr(space, "edit_tree", None)
        if not edit_tree or edit_tree.bl_idname != "GeometryNodeTree":
            return

        zones = (
            ("Simulation", "GeometryNodeSimulationInput", "GeometryNodeSimulationOutput", "node.add_zone", "Simulation zone", True),
            ("Repeat", "GeometryNodeRepeatInput", "GeometryNodeRepeatOutput", "node.add_zone", "Repeat zone", True),
            ("For Each Element", "GeometryNodeForeachGeometryElementInput", "GeometryNodeForeachGeometryElementOutput", "node.add_zone", "For Each Element zone", False),
            ("Closure", "NodeClosureInput", "NodeClosureOutput", "node.add_zone", "Closure zone", False),
        )
        for english, input_type, output_type, operator_id, description, add_default_geometry_link in zones:
            key = ("ZONE", input_type, output_type)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            chinese = _translation_label(english)
            label = _entry_label(english, chinese)
            add_entry(
                NodeSearchEntry(
                    identifier=_safe_identifier("Z", english, input_type, output_type),
                    category="Simulation" if english != "Closure" else "Utilities > Closure",
                    english=english,
                    chinese=chinese,
                    label=label,
                    description=description,
                    kind="ZONE",
                    node_type=operator_id,
                    search_text=_make_search_text(english, chinese, label, input_type),
                    settings=(
                        ("input_node_type", input_type),
                        ("output_node_type", output_type),
                        ("add_default_geometry_link", add_default_geometry_link),
                    ),
                )
            )

    cached_entries = _load_search_index_cache(context) or _load_bundled_search_index(context)
    if cached_entries is not None:
        for entry in cached_entries:
            add_entry(entry)
            remember_key(entry)
        add_zone_entries()
        add_asset_library_entries()
        add_local_groups()
        return

    cacheable_entries: list[NodeSearchEntry] = []

    def add_cacheable_entry(entry: NodeSearchEntry):
        cacheable_entries.append(entry)
        add_entry(entry)

    def add_builtin_entry(node_type: str, category: str = "Node", variant_label: str = "", settings=(), trusted_menu=False, variant_chinese: str = ""):
        key = (node_type, tuple(settings))
        if key in seen_keys:
            return
        if not trusted_menu and not _node_tree_allows_node(context, node_type):
            return

        seen_keys.add(key)

        bl_rna = bpy.types.Node.bl_rna_get_subclass(node_type)
        base_english = bl_rna.name if bl_rna and bl_rna.name else node_type
        base_chinese = _translation_label(base_english)
        if variant_label:
            english = f"{base_english} > {variant_label}"
            translated_variant = variant_chinese or _translation_label(variant_label)
            chinese = f"{base_chinese} > {translated_variant}"
        else:
            english = base_english
            chinese = base_chinese
        label = _entry_label(english, chinese)
        description = bl_rna.description if bl_rna and bl_rna.description else english
        add_cacheable_entry(
            NodeSearchEntry(
                identifier=_safe_identifier("N", node_type, english, repr(settings)),
                category=category,
                english=english,
                chinese=chinese,
                label=label,
                description=description,
                kind="NODE",
                node_type=node_type,
                search_text=_make_search_text(english, chinese, label, node_type),
                settings=tuple(settings),
            )
        )

    for node_type, category, variant_label, variant_chinese, settings in _iter_menu_entries(context):
        add_builtin_entry(node_type, category, variant_label, settings, trusted_menu=True, variant_chinese=variant_chinese)

    for cls in sorted(_iter_node_classes(), key=lambda item: getattr(item, "bl_label", "")):
        add_builtin_entry(cls.bl_idname)

    add_zone_entries()
    add_asset_library_entries(cacheable_entries)
    _save_search_index_cache(context, cacheable_entries)
    add_local_groups()


def _score_entry(entry: NodeSearchEntry, query: str, favorites: set[str]) -> int | None:
    query = _normalize(query)
    if not query:
        return None

    text = entry.search_text
    compact_text = text.replace(" ", "")
    compact_query = query.replace(" ", "")
    tokens = query.split()

    match = _query_match_parts(entry, query)
    english = match["english"]
    chinese = match["chinese"]
    english_parts = match["english_parts"]
    chinese_parts = match["chinese_parts"]
    category_match = match["category_match"]
    all_parts = english_parts + chinese_parts

    preferred_order = _officialish_preferred_order(entry, query)
    # Compact matching is intentionally narrow. Without this guard, short queries
    # can match across word boundaries, for example "set" in "Noise Texture".
    compact_match = bool(len(compact_query) >= 5 and " " in query and compact_query in compact_text)
    if preferred_order < 10_000:
        score = 110
    elif all(token in text for token in tokens):
        score = 100
    elif category_match:
        score = 90
    elif compact_match:
        score = 80
    elif match["ordered_leaf_match"] or match["ordered_search_match"]:
        score = 72
    else:
        return None

    if english == query:
        score += 1300
    elif chinese == query:
        score += 1300
    elif english.startswith(query):
        score += 450
    elif chinese.startswith(query):
        score += 450
    elif query in english:
        score += 250
    elif query in chinese:
        score += 250

    if all_parts:
        leaf_parts = match["leaf_parts"]
        root_parts = match["root_parts"]
        display_depth = _entry_display_depth(entry)
        if match["leaf_exact"]:
            score += 760
        elif match["leaf_prefix"]:
            score += 260
        elif match["root_exact"]:
            score += 100
        elif match["leaf_contains"]:
            score += 180
        elif match["ordered_leaf_match"]:
            score += 130
        elif match["ordered_search_match"]:
            score += 70

        is_primary_entry = match["is_primary"]
        if is_primary_entry and category_match:
            score += 520
        elif category_match:
            score += 40
        if is_primary_entry and match["leaf_contains"]:
            score += 360

        if match["leaf_exact"] or match["leaf_prefix"]:
            score += max(0, 7 - display_depth) * 95
        elif match["leaf_contains"] or match["ordered_leaf_match"]:
            score += max(0, 7 - display_depth) * 45

    if entry.identifier in favorites:
        score += 60

    return score


def _search_entries(query: str, favorites: set[str]) -> list[NodeSearchEntry]:
    scored = []

    for index, entry in enumerate(NODE_SEARCH_ENTRIES):
        score = _score_entry(entry, query, favorites)
        if score is None:
            continue
        bucket = _officialish_sort_bucket(entry, query)
        primary_order = _primary_match_order(entry, _normalize(query))
        preferred_order = _officialish_preferred_order(entry, query)
        scored.append((score, entry.identifier in favorites, entry.english.lower(), index, bucket, primary_order, preferred_order, entry))

    def sort_key(item):
        entry = item[7]
        match = _query_match_parts(entry, query)
        output_sort = entry.english.lower() if _has_visible_output_setting(entry) and match["root_word_match"] else ""
        return (not item[1], item[6], item[4], item[5], output_sort, item[3], -item[0], item[2])

    scored.sort(key=sort_key)
    return [item[-1] for item in scored]


def _store_cursor_location(context, event):
    space = context.space_data
    if not space or not getattr(space, "edit_tree", None):
        return

    if context.region and context.region.type == "WINDOW":
        area = context.area
        horizontal_pad = int(area.width / 10)
        vertical_pad = int(area.height / 10)
        x = min(max(horizontal_pad, event.mouse_region_x), area.width - horizontal_pad)
        y = min(max(vertical_pad, event.mouse_region_y), area.height - vertical_pad)
        space.cursor_location_from_region(x, y)
    else:
        space.cursor_location = space.edit_tree.view_center


def _add_builtin_node(context, entry: NodeSearchEntry):
    space = context.space_data
    edit_tree = space.edit_tree

    try:
        node = edit_tree.nodes.new(type=entry.node_type)
    except RuntimeError as ex:
        raise RuntimeError(str(ex)) from ex

    for selected_node in edit_tree.nodes:
        selected_node.select = False

    node.location = space.cursor_location
    node.select = True
    edit_tree.nodes.active = node
    _apply_node_settings(node, entry.settings)

    return node


def _apply_node_settings(node, settings: tuple[tuple[str, str], ...]):
    for name, value in settings:
        try:
            if name.startswith("inputs["):
                continue
            if name == "visible_output":
                if hasattr(node, "visible_output"):
                    setattr(node, name, value)
                continue
            setattr(node, name, value)
        except Exception:
            pass


def _load_asset_node_group(entry: NodeSearchEntry):
    existing = bpy.data.node_groups.get(entry.asset_name)
    if existing:
        return existing

    try:
        with bpy.data.libraries.load(entry.asset_path, link=False, assets_only=True) as (_data_from, data_to):
            data_to.node_groups = [entry.asset_name]
    except TypeError:
        with bpy.data.libraries.load(entry.asset_path, link=False) as (_data_from, data_to):
            data_to.node_groups = [entry.asset_name]

    return bpy.data.node_groups.get(entry.asset_name)


def _add_asset_node(context, entry: NodeSearchEntry):
    node_group = _load_asset_node_group(entry)
    if not node_group:
        return None

    space = context.space_data
    edit_tree = space.edit_tree

    from nodeitems_builtins import node_tree_group_type

    node_type = node_tree_group_type.get(edit_tree.bl_idname, "GeometryNodeGroup")
    node = edit_tree.nodes.new(type=node_type)
    node.node_tree = node_group

    for selected_node in edit_tree.nodes:
        selected_node.select = False

    node.location = space.cursor_location
    node.select = True
    edit_tree.nodes.active = node

    return node


def _add_zone(context, entry: NodeSearchEntry):
    kwargs = {name: value for name, value in entry.settings}
    try:
        result = bpy.ops.node.add_zone("EXEC_DEFAULT", **kwargs)
    except Exception:
        return None
    if "FINISHED" not in result:
        return None
    return getattr(context.space_data.edit_tree.nodes, "active", None)


def _draw_rect(x: float, y: float, width: float, height: float, color: tuple[float, float, float, float]):
    shader = gpu.shader.from_builtin("UNIFORM_COLOR")
    vertices = ((x, y), (x + width, y), (x + width, y + height), (x, y + height))
    batch = batch_for_shader(shader, "TRI_FAN", {"pos": vertices})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def _draw_horizontal_fade(x: float, y: float, width: float, height: float, color: tuple[float, float, float, float], steps: int = 10):
    if width <= 0 or height <= 0:
        return

    previous_blend = None
    try:
        previous_blend = gpu.state.blend_get()
        gpu.state.blend_set("ALPHA")
    except Exception:
        previous_blend = None

    try:
        step_width = width / steps
        for step in range(steps):
            alpha = color[3] * ((step + 1) / steps)
            _draw_rect(x + step * step_width, y, step_width + 1, height, (color[0], color[1], color[2], alpha))
    finally:
        try:
            gpu.state.blend_set(previous_blend if previous_blend is not None else "NONE")
        except Exception:
            pass


def _draw_right_rounded_fill(x: float, y: float, width: float, height: float, radius: float, color: tuple[float, float, float, float]):
    if width <= 0 or height <= 0:
        return

    radius = max(0, min(radius, width / 2, height / 2))
    if width > radius:
        _draw_rect(x, y, width - radius, height, color)
    cap_width = min(width, radius * 2)
    _draw_rounded_rect(x + width - cap_width, y, cap_width, height, radius, color)


def _rounded_rect_vertices(x: float, y: float, width: float, height: float, radius: float, segments: int = 8):
    radius = max(0, min(radius, width / 2, height / 2))
    corners = (
        (x + width - radius, y + height - radius, 0, math.pi / 2),
        (x + radius, y + height - radius, math.pi / 2, math.pi),
        (x + radius, y + radius, math.pi, math.pi * 1.5),
        (x + width - radius, y + radius, math.pi * 1.5, math.pi * 2),
    )
    vertices = [(x + width / 2, y + height / 2)]

    for cx, cy, start, end in corners:
        for step in range(segments + 1):
            angle = start + (end - start) * (step / segments)
            vertices.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))

    vertices.append(vertices[1])
    return vertices


def _draw_rounded_rect(
    x: float,
    y: float,
    width: float,
    height: float,
    radius: float,
    color: tuple[float, float, float, float],
):
    shader = gpu.shader.from_builtin("UNIFORM_COLOR")
    batch = batch_for_shader(shader, "TRI_FAN", {"pos": _rounded_rect_vertices(x, y, width, height, radius)})
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)


def _draw_rounded_panel(
    x: float,
    y: float,
    width: float,
    height: float,
    radius: float,
    fill: tuple[float, float, float, float],
    border: tuple[float, float, float, float] = BORDER_COLOR,
):
    _draw_rounded_rect(x, y, width, height, radius, border)
    _draw_rounded_rect(x + 1, y + 1, width - 2, height - 2, max(0, radius - 1), fill)


def _draw_text(text: str, x: float, y: float, size: int, color: tuple[float, float, float, float]):
    blf.size(FONT_ID, size)
    blf.color(FONT_ID, *color)
    blf.position(FONT_ID, x, y, 0)
    blf.draw(FONT_ID, text)


def _draw_label_text(label: str, x: float, y: float, max_width: float, size: int, secondary_color: tuple[float, float, float, float] = SECONDARY_TEXT_COLOR):
    if " / " not in label:
        _draw_text(_clip_text(label, max_width, size), x, y, size, TEXT_COLOR)
        return

    primary, secondary = label.split(" / ", 1)
    separator = " / "
    primary_width = _text_width(primary, size)
    separator_width = _text_width(separator, size)
    if primary_width + separator_width >= max_width:
        _draw_text(_clip_text(primary, max_width, size), x, y, size, TEXT_COLOR)
        return

    _draw_text(primary, x, y, size, TEXT_COLOR)
    secondary_x = x + primary_width
    secondary_text = _clip_text(separator + secondary, max_width - primary_width, size)
    _draw_text(secondary_text, secondary_x, y, size, secondary_color)


def _draw_centered_text(text: str, x: float, y: float, width: float, height: float, size: int, color: tuple[float, float, float, float]):
    blf.size(FONT_ID, size)
    text_width, text_height = blf.dimensions(FONT_ID, text)
    _draw_text(text, x + (width - text_width) / 2, y + (height - text_height) / 2, size, color)


def _draw_text_vcenter(text: str, x: float, y: float, height: float, size: int, color: tuple[float, float, float, float]):
    blf.size(FONT_ID, size)
    _text_width_value, text_height = blf.dimensions(FONT_ID, text)
    _draw_text(text, x, y + (height - text_height) / 2, size, color)


def _text_width(text: str, size: int) -> float:
    blf.size(FONT_ID, size)
    return blf.dimensions(FONT_ID, text)[0]


def _abbreviate_label(label: str, max_chars: int = 12) -> str:
    label = label.split(" / ")[0].split(" > ")[0].strip()
    if len(label) <= max_chars:
        return label

    words = label.split()
    if len(words) >= 2:
        first = words[0][:4]
        last = words[-1][: max(3, max_chars - len(first) - 2)]
        return f"{first}. {last}"

    return f"{label[: max_chars - 1]}."


def _fit_text(text: str, max_width: float, size: int) -> str:
    if _text_width(text, size) <= max_width:
        return text
    ellipsis = "."
    trimmed = text
    while trimmed and _text_width(trimmed + ellipsis, size) > max_width:
        trimmed = trimmed[:-1]
    return (trimmed + ellipsis) if trimmed else ellipsis


def _clip_text(text: str, max_width: float, size: int) -> str:
    if max_width <= 0:
        return ""
    if _text_width(text, size) <= max_width:
        return text
    clipped = text
    while clipped and _text_width(clipped, size) > max_width:
        clipped = clipped[:-1]
    return clipped


class ENS_AddNodeByEnglishSearch(Operator):
    bl_idname = "node.node_console"
    bl_label = "Node Console"
    bl_description = "Search and add nodes by English name"
    bl_options = {"REGISTER", "UNDO"}

    _draw_handler = None
    _query = ""
    _selected_index = 0
    _results: list[NodeSearchEntry] = []
    _favorites: set[str] = set()
    _favorite_meta: dict[str, str] = {}
    _panel_rect = (0, 0, 0, 0)
    _rows_top = 0
    _row_height = ROW_HEIGHT
    _padding = PANEL_PADDING
    _search_height = SEARCH_HEIGHT
    _clear_button_rect = (0, 0, 0, 0)
    _context_menu_index = None
    _context_menu_rect = (0, 0, 0, 0)
    _context_menu_hover = None
    _anchor_x = 0
    _anchor_y = 0
    _panel_x = None
    _search_y = None
    _placing_node = None
    _scroll_offset = 0
    _scroll_remainder = 0.0
    _visible_limit = MAX_RESULTS
    _shortcuts: list[str] = []
    _shortcut_rects: list[tuple[str, tuple[float, float, float, float]]] = []
    _shortcut_delete_rects: list[tuple[str, tuple[float, float, float, float]]] = []
    _shortcut_hover = None
    _shortcut_delete_hover = None
    _shortcut_hover_started = 0.0
    _hovered_result_index = None
    _keyboard_selection_active = False
    _pending_native_transform = False
    _timer = None

    @classmethod
    def poll(cls, context):
        space = context.space_data
        if not space or space.type != "NODE_EDITOR":
            return False
        return bool(getattr(space, "edit_tree", None) or getattr(space, "node_tree", None))

    def _refresh_results(self):
        self._results = _search_entries(self._query, self._favorites)
        self._context_menu_index = None
        self._scroll_offset = min(self._scroll_offset, max(0, len(self._results) - 1))
        if not self._results:
            self._selected_index = 0
            return
        self._selected_index = max(0, min(self._selected_index, len(self._results) - 1))

    def _finish(self, context, result):
        if self._draw_handler is not None:
            SpaceNodeEditor.draw_handler_remove(self._draw_handler, "WINDOW")
            self._draw_handler = None
        if self._timer is not None:
            try:
                context.window_manager.event_timer_remove(self._timer)
            except Exception:
                pass
            self._timer = None
        self._placing_node = None
        self._pending_native_transform = False
        if context.area:
            context.area.tag_redraw()
        return result

    def _hide_console(self, context):
        if self._draw_handler is not None:
            SpaceNodeEditor.draw_handler_remove(self._draw_handler, "WINDOW")
            self._draw_handler = None
        if context.area:
            context.area.tag_redraw()

    def _move_placing_node(self, context, event):
        if not self._placing_node:
            return
        space = context.space_data
        if event and context.region and context.region.type == "WINDOW":
            space.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
        self._placing_node.location = space.cursor_location

    def _start_native_node_transform(self, context) -> bool:
        try:
            result = bpy.ops.node.translate_attach_remove_on_cancel("INVOKE_DEFAULT")
            return "RUNNING_MODAL" in result or "FINISHED" in result
        except Exception:
            return False

    def _begin_placement(self, context, event, node):
        self._hide_console(context)
        self._placing_node = node
        self._move_placing_node(context, event)

        if event and event.type == "LEFTMOUSE" and event.value == "PRESS":
            self._pending_native_transform = True
            return {"RUNNING_MODAL"}

        if self._start_native_node_transform(context):
            return self._finish(context, {"FINISHED"})

        return {"RUNNING_MODAL"}

    def _cancel_placement(self, context):
        node = self._placing_node
        self._placing_node = None
        if node:
            try:
                node.id_data.nodes.remove(node)
            except Exception:
                pass
        return self._finish(context, {"CANCELLED"})

    def _confirm(self, context, event):
        if not self._results:
            return self._finish(context, {"CANCELLED"})

        entry = self._results[self._selected_index]
        if entry.kind == "NODE":
            try:
                node = _add_builtin_node(context, entry)
                return self._begin_placement(context, event, node)
            except RuntimeError as ex:
                self.report({"ERROR"}, str(ex))
                return self._finish(context, {"CANCELLED"})

        if entry.kind == "ASSET":
            result = _add_asset_node(context, entry)
            if result:
                return self._begin_placement(context, event, result)

            self.report({"ERROR"}, f"Unable to add asset node: {entry.asset_name}")
            return self._finish(context, {"CANCELLED"})

        if entry.kind == "ZONE":
            result = _add_zone(context, entry)
            if result:
                return self._begin_placement(context, event, result)

            self.report({"ERROR"}, f"Unable to add zone: {entry.english}")
            return self._finish(context, {"CANCELLED"})

        return self._finish(context, {"CANCELLED"})

    def _row_index_from_mouse(self, event):
        x, y, width, height = self._panel_rect
        mouse_x = event.mouse_region_x
        mouse_y = event.mouse_region_y
        rows_top = self._rows_top

        if mouse_x < x or mouse_x > x + width:
            return None
        if mouse_y > rows_top or mouse_y < y + self._padding:
            return None

        index = self._scroll_offset + int((rows_top - mouse_y) // self._row_height)
        if self._scroll_offset <= index < min(len(self._results), self._scroll_offset + self._visible_limit):
            return index
        return None

    def _shortcut_identifier_from_mouse(self, event):
        for identifier, rect in self._shortcut_rects:
            x, y, width, height = rect
            if x <= event.mouse_region_x <= x + width and y <= event.mouse_region_y <= y + height:
                return identifier
        return None

    def _shortcut_delete_identifier_from_mouse(self, event):
        for identifier, rect in self._shortcut_delete_rects:
            x, y, width, height = rect
            if x <= event.mouse_region_x <= x + width and y <= event.mouse_region_y <= y + height:
                return identifier
        return None

    def _update_shortcut_hover(self, event):
        delete_identifier = self._shortcut_delete_identifier_from_mouse(event)
        identifier = self._shortcut_identifier_from_mouse(event)
        self._shortcut_delete_hover = delete_identifier
        if identifier != self._shortcut_hover:
            self._shortcut_hover = identifier
            self._shortcut_hover_started = time.monotonic() if identifier else 0.0

    def _entry_from_identifier(self, identifier: str):
        return NODE_ENTRY_BY_ID.get(identifier)

    def _mouse_in_panel(self, event):
        x, y, width, height = self._panel_rect
        return x <= event.mouse_region_x <= x + width and y <= event.mouse_region_y <= y + height

    def _clear_button_from_mouse(self, event) -> bool:
        if not self._query:
            return False
        x, y, width, height = self._clear_button_rect
        return x <= event.mouse_region_x <= x + width and y <= event.mouse_region_y <= y + height

    def _clear_query(self):
        self._query = ""
        self._selected_index = 0
        self._scroll_offset = 0
        self._scroll_remainder = 0.0
        self._hovered_result_index = None
        self._keyboard_selection_active = False
        self._refresh_results()

    def _context_menu_action_from_mouse(self, event):
        x, y, width, height = self._context_menu_rect
        mouse_x = event.mouse_region_x
        mouse_y = event.mouse_region_y
        if mouse_x < x or mouse_x > x + width or mouse_y < y or mouse_y > y + height:
            return None

        row = int((y + height - mouse_y) // (height / 3))
        return ("FAVORITE", "UNFAVORITE", "SHORTCUT")[max(0, min(2, row))]

    def _update_context_menu_hover(self, event):
        self._context_menu_hover = self._context_menu_action_from_mouse(event)

    def _set_favorite(self, index, should_favorite: bool):
        if index is None or index >= len(self._results):
            return

        entry = self._results[index]
        identifier = entry.identifier
        if should_favorite:
            self._favorites.add(identifier)
            self._favorite_meta[identifier] = entry.label
        else:
            self._favorites.discard(identifier)
            self._favorite_meta.pop(identifier, None)
        _save_favorites(self._favorites, self._favorite_meta)
        self._refresh_results()

    def _open_context_menu(self, event, index):
        if index is None:
            return

        self._context_menu_index = index
        scale = _ui_scale()
        width = _scaled(CONTEXT_MENU_WIDTH, scale)
        row_height = _scaled(CONTEXT_MENU_ROW_HEIGHT, scale)
        x = event.mouse_region_x
        y = event.mouse_region_y - row_height * 3
        if self._panel_rect[2]:
            panel_x, panel_y, panel_width, panel_height = self._panel_rect
            x = min(max(panel_x, x), panel_x + panel_width - width)
            y = min(max(panel_y, y), panel_y + panel_height - row_height * 3)
        self._context_menu_rect = (x, y, width, row_height * 3)
        self._context_menu_hover = self._context_menu_action_from_mouse(event)

    def _scroll_results(self, amount: int) -> bool:
        if not self._query or not self._results or self._visible_limit <= 0:
            return False

        max_scroll = max(0, len(self._results) - self._visible_limit)
        old_offset = self._scroll_offset
        self._scroll_offset = min(max(0, self._scroll_offset + amount), max_scroll)
        if self._selected_index < self._scroll_offset:
            self._selected_index = self._scroll_offset
        elif self._selected_index >= self._scroll_offset + self._visible_limit:
            self._selected_index = self._scroll_offset + self._visible_limit - 1
        self._selected_index = max(0, min(self._selected_index, len(self._results) - 1))
        return self._scroll_offset != old_offset

    def _scroll_amount_from_event(self, event) -> int:
        if event.type in {"WHEELDOWNMOUSE", "WHEELOUTMOUSE"}:
            self._scroll_remainder = 0.0
            return -1
        if event.type in {"WHEELUPMOUSE", "WHEELINMOUSE"}:
            self._scroll_remainder = 0.0
            return 1
        if event.type in {"TRACKPADPAN", "MOUSEPAN"}:
            delta_y = getattr(event, "mouse_prev_y", event.mouse_region_y) - getattr(event, "mouse_y", event.mouse_region_y)
            if delta_y == 0:
                delta_y = getattr(event, "mouse_prev_y", event.mouse_region_y) - event.mouse_region_y
            if delta_y == 0:
                return 0

            row_step = max(16.0, self._row_height * 0.9)
            self._scroll_remainder += -delta_y / row_step
            amount = int(self._scroll_remainder)
            if amount == 0:
                return 0

            amount = max(-1, min(1, amount))
            self._scroll_remainder -= amount
            return amount
        return 0

    def invoke(self, context, event):
        _store_cursor_location(context, event)
        _rebuild_search_entries(context)

        if not NODE_SEARCH_ENTRIES:
            self.report({"WARNING"}, "No addable nodes found for the current node tree")
            return {"CANCELLED"}

        self._query = ""
        self._selected_index = 0
        self._context_menu_index = None
        self._context_menu_hover = None
        self._anchor_x = event.mouse_region_x
        self._anchor_y = event.mouse_region_y
        self._panel_x = None
        self._search_y = None
        self._favorites = _load_favorites()
        self._favorite_meta = _load_favorite_meta()
        self._shortcuts = _load_shortcuts()
        self._shortcut_hover_started = 0.0
        self._scroll_offset = 0
        self._scroll_remainder = 0.0
        self._hovered_result_index = None
        self._keyboard_selection_active = False
        self._pending_native_transform = False
        self._refresh_results()
        self._draw_handler = SpaceNodeEditor.draw_handler_add(self._draw_callback, (context,), "WINDOW", "POST_PIXEL")
        self._timer = context.window_manager.event_timer_add(0.2, window=context.window)
        context.window_manager.modal_handler_add(self)
        if context.area:
            context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type == "TIMER":
            if context.area:
                context.area.tag_redraw()
            return {"RUNNING_MODAL"}

        if self._placing_node and self._pending_native_transform:
            if event.value == "PRESS" and event.type == "ESC":
                return self._cancel_placement(context)
            if event.type == "LEFTMOUSE" and event.value == "RELEASE":
                self._pending_native_transform = False
                if self._start_native_node_transform(context):
                    return self._finish(context, {"FINISHED"})
            return {"RUNNING_MODAL"}

        if self._placing_node:
            if event.type == "MOUSEMOVE":
                self._move_placing_node(context, event)
                if context.area:
                    context.area.tag_redraw()
                return {"RUNNING_MODAL"}

            if event.value == "PRESS":
                if event.type == "ESC":
                    return self._cancel_placement(context)
                if event.type in {"LEFTMOUSE", "RET", "NUMPAD_ENTER"}:
                    self._move_placing_node(context, event)
                    return self._finish(context, {"FINISHED"})

            return {"RUNNING_MODAL"}

        if event.value == "PRESS" and event.type == "V" and (event.ctrl or event.oskey):
            clipboard = getattr(context.window_manager, "clipboard", "")
            if clipboard:
                self._query += clipboard
                self._hovered_result_index = None
                self._keyboard_selection_active = False
                self._refresh_results()
                if context.area:
                    context.area.tag_redraw()
            return {"RUNNING_MODAL"}

        if event.unicode and not event.ctrl and not event.alt and not event.oskey and event.type not in {"RET", "NUMPAD_ENTER", "ESC", "BACK_SPACE", "DEL"}:
            self._query += event.unicode
            self._hovered_result_index = None
            self._keyboard_selection_active = False
            self._refresh_results()
            if context.area:
                context.area.tag_redraw()
            return {"RUNNING_MODAL"}

        if event.type in {"WHEELUPMOUSE", "WHEELDOWNMOUSE", "WHEELINMOUSE", "WHEELOUTMOUSE", "TRACKPADPAN", "MOUSEPAN"}:
            if self._context_menu_index is not None:
                return {"RUNNING_MODAL"}
            amount = self._scroll_amount_from_event(event)
            if amount:
                self._scroll_results(amount)
                if context.area:
                    context.area.tag_redraw()
            return {"RUNNING_MODAL"}

        if event.value == "PRESS":
            if event.type in {"ESC"}:
                return self._finish(context, {"CANCELLED"})

            if event.type in {"RET", "NUMPAD_ENTER"}:
                if self._placing_node:
                    return self._finish(context, {"FINISHED"})
                return self._confirm(context, event)

            if event.type == "UP_ARROW":
                self._selected_index = max(0, self._selected_index - 1)
                self._hovered_result_index = None
                self._keyboard_selection_active = True
                self._scroll_offset = min(self._scroll_offset, self._selected_index)
            elif event.type == "DOWN_ARROW":
                self._selected_index = min(max(0, len(self._results) - 1), self._selected_index + 1)
                self._hovered_result_index = None
                self._keyboard_selection_active = True
                if self._selected_index >= self._scroll_offset + self._visible_limit:
                    self._scroll_offset = self._selected_index - self._visible_limit + 1
            elif event.type == "BACK_SPACE":
                self._query = self._query[:-1]
                self._hovered_result_index = None
                self._keyboard_selection_active = False
                self._refresh_results()
            elif event.type == "DEL":
                self._clear_query()
            elif event.type == "LEFTMOUSE":
                if self._context_menu_index is not None:
                    action = self._context_menu_action_from_mouse(event)
                    entry = self._results[self._context_menu_index] if self._context_menu_index < len(self._results) else None
                    if action == "FAVORITE":
                        self._set_favorite(self._context_menu_index, True)
                    elif action == "UNFAVORITE":
                        self._set_favorite(self._context_menu_index, False)
                    elif action == "SHORTCUT" and entry:
                        _add_shortcut(entry.identifier)
                        self._favorite_meta[entry.identifier] = entry.label
                        _save_favorites(self._favorites, self._favorite_meta)
                        self._shortcuts = _load_shortcuts()
                        self._context_menu_index = None
                        self._query = ""
                        self._scroll_offset = 0
                        self._refresh_results()
                    else:
                        self._context_menu_index = None
                        if not self._mouse_in_panel(event):
                            return self._finish(context, {"CANCELLED"})
                    if context.area:
                        context.area.tag_redraw()
                    return {"RUNNING_MODAL"}

                if self._clear_button_from_mouse(event):
                    self._clear_query()
                    if context.area:
                        context.area.tag_redraw()
                    return {"RUNNING_MODAL"}

                index = self._row_index_from_mouse(event)
                if index is not None:
                    self._selected_index = index
                    return self._confirm(context, event)

                shortcut_delete_identifier = self._shortcut_delete_identifier_from_mouse(event)
                if shortcut_delete_identifier:
                    _remove_shortcut(shortcut_delete_identifier)
                    self._shortcuts = _load_shortcuts()
                    self._shortcut_hover = None
                    self._shortcut_delete_hover = None
                    if context.area:
                        context.area.tag_redraw()
                    return {"RUNNING_MODAL"}

                shortcut_identifier = self._shortcut_identifier_from_mouse(event)
                if shortcut_identifier:
                    entry = self._entry_from_identifier(shortcut_identifier)
                    if entry:
                        self._results = [entry]
                        self._selected_index = 0
                        return self._confirm(context, event)
                if not self._mouse_in_panel(event):
                    return self._finish(context, {"CANCELLED"})
            elif event.type == "RIGHTMOUSE":
                self._open_context_menu(event, self._row_index_from_mouse(event))
            elif event.type == "MOUSEMOVE":
                if self._context_menu_index is not None:
                    self._update_context_menu_hover(event)
                    if context.area:
                        context.area.tag_redraw()
                    return {"RUNNING_MODAL"}

                index = self._row_index_from_mouse(event)
                self._hovered_result_index = index
                if index is not None:
                    self._selected_index = index
                    self._keyboard_selection_active = False
                old_hover = self._shortcut_hover
                old_delete_hover = self._shortcut_delete_hover
                self._update_shortcut_hover(event)
                if (old_hover != self._shortcut_hover or old_delete_hover != self._shortcut_delete_hover) and context.area:
                    context.area.tag_redraw()

            if context.area:
                context.area.tag_redraw()
            return {"RUNNING_MODAL"}

        if event.type == "MOUSEMOVE":
            if self._context_menu_index is not None:
                old_hover = self._context_menu_hover
                self._update_context_menu_hover(event)
                if old_hover != self._context_menu_hover and context.area:
                    context.area.tag_redraw()
                return {"RUNNING_MODAL"}

            index = self._row_index_from_mouse(event)
            old_result_hover = self._hovered_result_index
            self._hovered_result_index = index
            if index is not None:
                self._keyboard_selection_active = False
            if index is not None and index != self._selected_index:
                self._selected_index = index
                if context.area:
                    context.area.tag_redraw()
            elif old_result_hover != self._hovered_result_index and context.area:
                context.area.tag_redraw()
            old_hover = self._shortcut_hover
            old_delete_hover = self._shortcut_delete_hover
            self._update_shortcut_hover(event)
            if (old_hover != self._shortcut_hover or old_delete_hover != self._shortcut_delete_hover) and context.area:
                context.area.tag_redraw()

        return {"RUNNING_MODAL"}

    def _draw_callback(self, context):
        region = context.region
        if not region:
            return

        scale = _ui_scale()
        padding = _scaled(PANEL_PADDING, scale)
        search_height = _scaled(SEARCH_HEIGHT, scale)
        row_height = _scaled(ROW_HEIGHT, scale)
        gap = _scaled(6, scale)
        shortcut_height = _scaled(SHORTCUT_HEIGHT, scale)
        shortcut_gap = _scaled(SHORTCUT_GAP, scale)
        radius = _scaled(5, scale)
        width = min(_scaled(PANEL_WIDTH, scale), region.width - _scaled(12, scale))
        has_query = bool(_normalize(self._query))
        search_width = width - padding * 2
        active_shortcuts = [identifier for identifier in self._shortcuts if identifier in NODE_ENTRY_BY_ID]
        shortcut_rows = 1 if active_shortcuts and not has_query else 0

        if self._panel_x is None:
            self._panel_x = self._anchor_x - padding - search_width * 0.75
        if self._search_y is None:
            self._search_y = self._anchor_y - search_height / 2

        x = min(max(1, self._panel_x), max(1, region.width - width - 1))
        preferred_rows_below = min(4, MAX_RESULTS)
        min_search_y = padding + gap + preferred_rows_below * row_height
        search_y = min(max(min_search_y, self._search_y), region.height - padding - search_height)
        max_rows_below = max(1, int((search_y - gap - padding) // row_height))
        visible_limit = min(MAX_RESULTS, max_rows_below)
        self._visible_limit = visible_limit
        rows = min(visible_limit, max(0, len(self._results) - self._scroll_offset)) if has_query else 0
        empty_rows = 1 if has_query and not self._results else 0
        shortcuts_height = shortcut_rows * (shortcut_gap + shortcut_height)
        height = padding * 2 + search_height + shortcuts_height + (gap + max(rows, empty_rows) * row_height if has_query else 0) + (_scaled(12, scale) if has_query and len(self._results) > rows else 0)
        y = search_y + search_height + padding - height
        self._panel_rect = (x, y, width, height)
        self._padding = padding
        self._search_height = search_height
        self._row_height = row_height

        _draw_rounded_panel(x, y, width, height, radius, PANEL_BACKGROUND)
        _draw_rounded_panel(x + padding, search_y, search_width, search_height, max(4, radius - 1), FIELD_BACKGROUND, BORDER_COLOR)

        placeholder = "搜索节点..." if _display_mode() in {"CHINESE", "CHINESE_ENGLISH"} else "Search nodes..."
        query_text = self._query if self._query else placeholder
        query_color = TEXT_COLOR if self._query else MUTED_TEXT_COLOR
        query_size = _scaled(13, scale)
        search_text_y = search_y + (search_height - _scaled(13, scale)) / 2 + _scaled(1, scale)
        _draw_text("⌕", x + padding + _scaled(10, scale), search_text_y - _scaled(2, scale), _scaled(18, scale), MUTED_TEXT_COLOR)
        query_x = x + padding + _scaled(34, scale)
        text_x = query_x if self._query else query_x + _scaled(9, scale)
        clear_size = max(_scaled(13, scale), 12)
        clear_x = x + padding + search_width - clear_size - _scaled(9, scale)
        clear_y = search_y + (search_height - clear_size) / 2
        if self._query:
            self._clear_button_rect = (clear_x - _scaled(4, scale), clear_y - _scaled(4, scale), clear_size + _scaled(8, scale), clear_size + _scaled(8, scale))
            text_max_width = max(0, clear_x - text_x - _scaled(10, scale))
        else:
            self._clear_button_rect = (0, 0, 0, 0)
            text_max_width = search_width - (text_x - (x + padding)) - _scaled(8, scale)
        _draw_text(_clip_text(query_text, text_max_width, query_size), text_x, search_text_y, query_size, query_color)
        if int(time.monotonic() * 2) % 2 == 0:
            cursor_x = query_x + min(_text_width(self._query, query_size), text_max_width) + _scaled(2, scale)
            _draw_rect(cursor_x, search_y + _scaled(5, scale), max(1, _scaled(1, scale)), search_height - _scaled(10, scale), TEXT_COLOR)
        if self._query:
            _draw_rounded_rect(clear_x, clear_y, clear_size, clear_size, clear_size / 2, (0.27, 0.27, 0.29, 0.90))
            _draw_centered_text("x", clear_x, clear_y, clear_size, clear_size, max(9, _scaled(9, scale)), (0.62, 0.62, 0.64, 0.95))

        self._shortcut_rects = []
        self._shortcut_delete_rects = []
        shortcuts_y = search_y - shortcut_gap - shortcut_height
        if active_shortcuts and not has_query:
            item_gap = _scaled(5, scale)
            item_width = (search_width - item_gap * (min(len(active_shortcuts), 10) - 1)) / min(len(active_shortcuts), 10)
            for index, identifier in enumerate(active_shortcuts[:10]):
                item_x = x + padding + index * (item_width + item_gap)
                rect = (item_x, shortcuts_y, item_width, shortcut_height)
                self._shortcut_rects.append((identifier, rect))
                entry = NODE_ENTRY_BY_ID[identifier]
                shortcut_hovered = self._shortcut_hover == identifier
                shortcut_fill, shortcut_border = _entry_type_colors(entry, active=shortcut_hovered)
                shortcut_fill = _blend_color(shortcut_fill, 1.0, FIELD_BACKGROUND)
                _draw_rounded_panel(item_x, shortcuts_y, item_width, shortcut_height, max(3, radius - 1), shortcut_fill, shortcut_border)
                shortcut_text_size = _scaled(11, scale)
                delete_size = max(_scaled(13, scale), 11)
                delete_x = item_x + item_width - delete_size - _scaled(4, scale)
                delete_y = shortcuts_y + shortcut_height - delete_size - _scaled(4, scale)
                delete_visible = self._shortcut_hover == identifier
                delete_hovered = False
                if delete_visible:
                    delete_rect = (delete_x, delete_y, delete_size, delete_size)
                    self._shortcut_delete_rects.append((identifier, delete_rect))
                shortcut_text = _fit_text(_abbreviate_label(_entry_primary_label(entry)), item_width - _scaled(18, scale), shortcut_text_size)
                _draw_text_vcenter(shortcut_text, item_x + _scaled(7, scale), shortcuts_y, shortcut_height, shortcut_text_size, TEXT_COLOR)
                if delete_visible:
                    x_size = max(10, _scaled(10, scale))
                    delete_hovered = self._shortcut_delete_hover == identifier
                    if delete_hovered:
                        _draw_rounded_rect(delete_x, delete_y, delete_size, delete_size, delete_size / 2, (0.42, 0.42, 0.44, 0.96))
                        x_color = (0.92, 0.92, 0.94, 1.0)
                    else:
                        x_color = (0.50, 0.50, 0.52, 0.82)
                    _draw_centered_text("x", delete_x, delete_y, delete_size, delete_size, x_size, x_color)

        rows_top = search_y - shortcuts_height - gap
        self._rows_top = rows_top
        if not has_query:
            return

        if not self._results:
            _draw_text("No results found", x + padding + _scaled(8, scale), rows_top - _scaled(20, scale), _scaled(13, scale), TEXT_COLOR)
            return

        visible_results = self._results[self._scroll_offset:self._scroll_offset + visible_limit]
        for visible_index, entry in enumerate(visible_results):
            index = self._scroll_offset + visible_index
            row_y = rows_top - (visible_index + 1) * row_height
            is_selected = index == self._selected_index
            is_hovered = index == self._hovered_result_index
            is_emphasized = is_selected and (is_hovered or self._keyboard_selection_active)
            is_favorite = entry.identifier in self._favorites

            row_text_y = row_y + _scaled(7, scale)
            category_x = x + padding + _scaled(10, scale)
            fav_width = _scaled(12, scale)
            fav_height = _scaled(18, scale)
            fav_x = x + width - padding - fav_width - _scaled(8, scale)
            fade_width = _scaled(46, scale)
            fade_x = fav_x - fade_width
            label_size = _scaled(13, scale)
            category_size = label_size
            display_category, display_label = _display_parts(entry)
            category_text = f"{display_category} ▸"
            category_text = category_text.replace(" > ", " ▸ ")
            category_text = _clip_text(category_text, max(0, fav_x - category_x), category_size)
            category_width = _text_width(category_text, category_size)
            label_gap = _scaled(10, scale)
            block_gap = _scaled(7, scale)
            label_x = category_x + category_width + label_gap
            label_max_width = max(0, fav_x - label_x)
            block_y = row_y + _scaled(2, scale)
            block_height = row_height - _scaled(4, scale)
            block_radius = max(3, radius - 2)
            category_block_x = x + padding
            category_block_width = max(_scaled(36, scale), label_x - category_block_x - block_gap)
            label_block_x = label_x - _scaled(3, scale)
            label_block_width = max(0, x + padding + search_width - label_block_x)
            category_fill, category_border = _entry_type_colors(entry, active=is_emphasized)
            _draw_rounded_panel(category_block_x, block_y, category_block_width, block_height, block_radius, category_fill, category_border)
            if is_emphasized:
                _draw_rounded_panel(label_block_x, block_y, label_block_width, block_height, block_radius, HIGHLIGHT_COLOR, HIGHLIGHT_BORDER_COLOR)

            muted_row_color = MUTED_TEXT_COLOR if is_emphasized else SECONDARY_TEXT_COLOR
            _draw_text(category_text, category_x, row_text_y, category_size, muted_row_color)
            _draw_label_text(display_label, label_x, row_text_y, label_max_width, label_size, muted_row_color)
            fade_color = HIGHLIGHT_COLOR if is_emphasized else PANEL_BACKGROUND
            _draw_horizontal_fade(fade_x, block_y, fade_width, block_height, fade_color, steps=10)
            _draw_right_rounded_fill(fav_x, block_y, max(0, x + width - padding - fav_x), block_height, block_radius, fade_color)
            if is_favorite:
                fav_y = row_y + (row_height - fav_height) / 2
                fav_color = (0.30, 0.30, 0.31, 0.86) if is_emphasized else (0.15, 0.15, 0.155, 0.78)
                _draw_rounded_rect(fav_x, fav_y, fav_width, fav_height, max(3, radius - 2), fav_color)

        if has_query and len(self._results) > self._scroll_offset + rows:
            _draw_text("▼", x + width / 2 - _scaled(4, scale), y + _scaled(4, scale), _scaled(12, scale), TEXT_COLOR)

        if self._context_menu_index is not None:
            menu_x, menu_y, menu_width, menu_height = self._context_menu_rect
            menu_row_height = menu_height / 3
            _draw_rounded_panel(menu_x, menu_y, menu_width, menu_height, radius, PANEL_BACKGROUND)
            labels = (("FAVORITE", "Add Favorite"), ("UNFAVORITE", "Remove Favorite"), ("SHORTCUT", "Add Shortcut"))
            for index, (action, label) in enumerate(labels):
                row_y = menu_y + menu_height - (index + 1) * menu_row_height
                if self._context_menu_hover == action:
                    _draw_rounded_panel(menu_x + 4, row_y + 3, menu_width - 8, menu_row_height - 6, max(3, radius - 2), HIGHLIGHT_COLOR, HIGHLIGHT_BORDER_COLOR)
                _draw_text(label, menu_x + _scaled(12, scale), row_y + _scaled(8, scale), _scaled(13, scale), TEXT_COLOR)

        if (
            self._shortcut_hover
            and self._shortcut_hover in NODE_ENTRY_BY_ID
            and time.monotonic() - self._shortcut_hover_started >= 1.0
        ):
            entry = NODE_ENTRY_BY_ID[self._shortcut_hover]
            tooltip_text = entry.label
            tooltip_width = _text_width(tooltip_text, _scaled(12, scale)) + _scaled(18, scale)
            tooltip_height = _scaled(24, scale)
            tooltip_x = min(max(x + padding, self._anchor_x), x + width - tooltip_width - padding)
            tooltip_y = shortcuts_y - tooltip_height - _scaled(4, scale)
            if tooltip_y < y + padding:
                tooltip_y = shortcuts_y + shortcut_height + _scaled(4, scale)
            _draw_rounded_panel(tooltip_x, tooltip_y, tooltip_width, tooltip_height, max(3, radius - 1), FIELD_BACKGROUND, BORDER_COLOR)
            _draw_text(tooltip_text, tooltip_x + _scaled(9, scale), tooltip_y + _scaled(7, scale), _scaled(12, scale), TEXT_COLOR)


class NODECONSOLE_OT_RefreshAssetIndex(Operator):
    bl_idname = "node_console.refresh_asset_index"
    bl_label = "Refresh Asset Index"
    bl_description = "Scan Blender asset node groups and cache them for fast search"
    bl_options = {"INTERNAL"}

    def execute(self, _context):
        count = _refresh_asset_index()
        self.report({"INFO"}, f"Node Console cached {count} asset node groups")
        return {"FINISHED"}


class NODECONSOLE_OT_RemoveFavorite(Operator):
    bl_idname = "node_console.remove_favorite"
    bl_label = "Remove Favorite"
    bl_description = "Remove this node from Node Console favorites"
    bl_options = {"INTERNAL"}

    identifier: StringProperty()

    def execute(self, _context):
        _remove_favorite(self.identifier)
        return {"FINISHED"}


class NODECONSOLE_OT_RemoveShortcut(Operator):
    bl_idname = "node_console.remove_shortcut"
    bl_label = "Remove Shortcut"
    bl_description = "Remove this node shortcut"
    bl_options = {"INTERNAL"}

    identifier: StringProperty()

    def execute(self, _context):
        _remove_shortcut(self.identifier)
        return {"FINISHED"}


class NODECONSOLE_OT_MoveShortcut(Operator):
    bl_idname = "node_console.move_shortcut"
    bl_label = "Move Shortcut"
    bl_description = "Move this shortcut"
    bl_options = {"INTERNAL"}

    identifier: StringProperty()
    direction: StringProperty(default="UP")

    def execute(self, _context):
        _move_shortcut(self.identifier, -1 if self.direction == "UP" else 1)
        return {"FINISHED"}


class ENS_AddonPreferences(AddonPreferences):
    bl_idname = ADDON_ID

    display_mode: EnumProperty(
        name="Search Result Display",
        description="How node names are shown in the custom search panel",
        items=(
            ("ENGLISH", "English", "Show only English names"),
            ("CHINESE", "中文", "Show only translated names where available"),
            ("ENGLISH_CHINESE", "English / 中文", "Show English names first with Chinese translations"),
            ("CHINESE_ENGLISH", "中文 / English", "Show Chinese translations first with English names"),
        ),
        default="ENGLISH_CHINESE",
        update=_preference_changed,
    )
    chinese_fuzzy_match: BoolProperty(
        name="Enable Chinese Fuzzy Match",
        description="Allow sparse Chinese/pinyin matching such as '设置法向' matching '设置曲线法向'. May make searching slightly slower.",
        default=False,
        update=_preference_changed,
    )
    shortcut_key: EnumProperty(
        name="Shortcut Key",
        description="Keyboard key used to open Node Console in the node editor",
        items=(
            ("A", "A", ""),
            ("F", "F", ""),
            ("SPACE", "Space", ""),
        ),
        default="A",
        update=_shortcut_changed,
    )
    shortcut_shift: BoolProperty(
        name="Shift",
        description="Require Shift for the Node Console shortcut",
        default=True,
        update=_shortcut_changed,
    )
    shortcut_ctrl: BoolProperty(
        name="Ctrl",
        description="Require Ctrl for the Node Console shortcut",
        default=False,
        update=_shortcut_changed,
    )
    shortcut_alt: BoolProperty(
        name="Alt",
        description="Require Alt for the Node Console shortcut",
        default=False,
        update=_shortcut_changed,
    )
    shortcut_oskey: BoolProperty(
        name="Command",
        description="Require Command for the Node Console shortcut on macOS",
        default=False,
        update=_shortcut_changed,
    )
    scan_asset_libraries: BoolProperty(
        name="Show Cached Asset Nodes",
        description="Show cached Asset Library node groups in search results. Refresh Asset Index updates the cache.",
        default=True,
        update=_preference_changed,
    )
    ui_scale: FloatProperty(
        name="Console Size",
        description="Adjust the Node Console text and panel size",
        default=1.0,
        min=0.5,
        max=2.0,
        soft_min=0.5,
        soft_max=2.0,
        step=10,
        update=_preference_changed,
    )
    favorites_json: StringProperty(
        name="Favorite Nodes",
        description="Internal favorite node storage",
        default="[]",
        options={"HIDDEN"},
    )
    favorite_meta_json: StringProperty(
        name="Favorite Node Names",
        description="Internal favorite node display names",
        default="{}",
        options={"HIDDEN"},
    )

    def draw(self, _context):
        layout = self.layout
        top = layout.split(factor=0.76)
        left_grid = top.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=False, align=True)
        left_grid.label(text="Search Result Display")
        left_grid.prop(self, "display_mode", text="")
        left_grid.prop(self, "chinese_fuzzy_match", text="Enable Chinese Fuzzy Match")
        left_grid.label(text="May slightly slow live search")
        left_grid.prop(self, "scan_asset_libraries", text="Show Cached Asset Nodes")
        left_grid.label(text=f"Cached Assets: {len(_load_asset_index())}")
        right_col = top.column(align=False)
        right_col.prop(self, "ui_scale")
        right_col.separator(factor=0.35)
        right_col.operator(NODECONSOLE_OT_RefreshAssetIndex.bl_idname, icon="FILE_REFRESH", text="Refresh Asset Index")

        box = layout.box()
        box.label(text="Shortcut")
        row = box.row(align=False)
        row.prop(self, "shortcut_key", text="", translate=False)
        row.separator(factor=1.0)
        if sys.platform == "darwin":
            row.prop(self, "shortcut_oskey", text="Command", toggle=True, translate=False)
            row.separator(factor=0.45)
        row.prop(self, "shortcut_ctrl", text="Ctrl", toggle=True, translate=False)
        row.separator(factor=0.45)
        row.prop(self, "shortcut_shift", text="Shift", toggle=True, translate=False)
        row.separator(factor=0.45)
        row.prop(self, "shortcut_alt", text="Alt", toggle=True, translate=False)

        favorite_meta = _load_favorite_meta()
        lists = layout.row(align=False)

        favorites = _load_favorites()
        left_col = lists.column()
        box = left_col.box()
        box.label(text="Favorites")
        if not favorites:
            box.label(text="No favorite nodes")
        else:
            for identifier in sorted(favorites, key=lambda item: _entry_display_label(item, favorite_meta.get(item, item)).lower()):
                row = box.row(align=True)
                row.label(text=_entry_display_label(identifier, favorite_meta.get(identifier, identifier)))
                remove_op = row.operator(NODECONSOLE_OT_RemoveFavorite.bl_idname, text="", icon="X")
                remove_op.identifier = identifier

        shortcuts = _load_shortcuts()
        lists.separator(factor=0.8)
        right_col = lists.column()
        box = right_col.box()
        box.label(text="Shortcuts")
        if not shortcuts:
            box.label(text="No node shortcuts")
        else:
            for identifier in shortcuts:
                row = box.row(align=True)
                row.label(text=_entry_display_label(identifier, favorite_meta.get(identifier, identifier)))
                up_op = row.operator(NODECONSOLE_OT_MoveShortcut.bl_idname, text="", icon="TRIA_UP")
                up_op.identifier = identifier
                up_op.direction = "UP"
                down_op = row.operator(NODECONSOLE_OT_MoveShortcut.bl_idname, text="", icon="TRIA_DOWN")
                down_op.identifier = identifier
                down_op.direction = "DOWN"
                remove_op = row.operator(NODECONSOLE_OT_RemoveShortcut.bl_idname, text="", icon="X")
                remove_op.identifier = identifier


classes = (
    ENS_AddNodeByEnglishSearch,
    NODECONSOLE_OT_RefreshAssetIndex,
    NODECONSOLE_OT_RemoveFavorite,
    NODECONSOLE_OT_RemoveShortcut,
    NODECONSOLE_OT_MoveShortcut,
    ENS_AddonPreferences,
)


def refresh_keymap():
    unregister_keymap()
    register_keymap()


def _remove_node_console_keymap_items():
    wm = bpy.context.window_manager
    for keyconfig in (wm.keyconfigs.addon, wm.keyconfigs.user):
        if not keyconfig:
            continue
        keymap = keyconfig.keymaps.get("Node Editor")
        if not keymap:
            continue
        stale_items = [item for item in keymap.keymap_items if item.idname == ENS_AddNodeByEnglishSearch.bl_idname]
        for item in stale_items:
            try:
                keymap.keymap_items.remove(item)
            except Exception:
                pass


def register_keymap():
    prefs = _preferences()

    keyconfig = bpy.context.window_manager.keyconfigs.addon
    if not keyconfig:
        return

    _remove_node_console_keymap_items()
    keymap = keyconfig.keymaps.new(name="Node Editor", space_type="NODE_EDITOR")

    key_type = prefs.shortcut_key if prefs else "A"
    shift = prefs.shortcut_shift if prefs else True
    ctrl = prefs.shortcut_ctrl if prefs else False
    alt = prefs.shortcut_alt if prefs else False
    oskey = prefs.shortcut_oskey if prefs else False
    keymap_item = keymap.keymap_items.new(
        ENS_AddNodeByEnglishSearch.bl_idname,
        type=key_type,
        value="PRESS",
        shift=shift,
        ctrl=ctrl,
        alt=alt,
        oskey=oskey,
    )
    KEYMAP_ITEMS.append((keymap, keymap_item))


def unregister_keymap():
    while KEYMAP_ITEMS:
        keymap, keymap_item = KEYMAP_ITEMS.pop()
        try:
            keymap.keymap_items.remove(keymap_item)
        except Exception:
            pass
    _remove_node_console_keymap_items()


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    _load_preferences_from_settings()
    register_keymap()


def unregister():
    global BACKGROUND_ASSET_INDEX
    BACKGROUND_ASSET_INDEX = None
    unregister_keymap()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
