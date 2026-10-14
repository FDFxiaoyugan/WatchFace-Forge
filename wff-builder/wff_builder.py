#!/usr/bin/env python3
"""
WFF Builder — Watch Face Format APK 构建引擎 (Agent-Friendly)

用法:
    python wff_builder.py build <project_dir>
    python wff_builder.py init <project_dir>
    python wff_builder.py validate <project_dir>

开发者只需提供:
    project.yaml    — 项目配置
    watchface.xml   — 表盘设计（WFF XML）
    preview.png     — 表盘预览图（尺寸=画布尺寸，如 450×450）


框架内置 WFF 规则校验:
    - watchface.xml 语法检查（16 条规则，覆盖所有已踩过的坑）
    - APK 结构校验（二进制 AXML / STORED 对齐）
    - 构建后自动验证
"""

import os
import sys
import zipfile
import subprocess
import struct
import zlib
import binascii
import json
import shutil
import hashlib
import re
import math
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

# ─── 配置 ──────────────────────────────────────────────

BUILDER_ROOT = Path(__file__).resolve().parent
ANDROID_HOME = os.environ.get("ANDROID_HOME", "/opt/android-sdk")
BUILD_TOOLS = Path(ANDROID_HOME) / "build-tools" / "34.0.0"
ANDROID_JAR = Path(ANDROID_HOME) / "platforms" / "android-34" / "android.jar"
AAPT2 = Path(os.environ.get("AAPT2", str(BUILD_TOOLS / "aapt2")))
APKSIGNER = Path(os.environ.get("APKSIGNER", str(BUILD_TOOLS / "apksigner")))

# ─── 签名配置（审计 S1 修复）──────────────────────────────
# 模式: WF_ENV=development（默认）| production
#   development — 使用仓库内公开开发证书（密码/alias 亦公开），显式配置
#                 WFF_KEYSTORE(+ALIAS/PASSWORD) 可覆盖为自定义密钥库。
#   production  — 必须显式提供外部签名，任一缺失即构建失败（fail-closed）：
#                 WFF_KEYSTORE / WFF_KEYSTORE_ALIAS
#                 WFF_KEYSTORE_PASSWORD 或 WFF_KEYSTORE_PASSWORD_FILE
#                 （可选 WFF_KEY_KEY_PASSWORD / _FILE，缺省同 store 密码）
#                 且证书 SHA-256 不得等于下方公开开发证书指纹——即使把
#                 test.keystore 换文件名也拒绝。
# 密码传递: apksigner/keytool 使用 env:/file: 引用形式, 不出现在 argv 明文。

WF_ENV = os.environ.get("WF_ENV", "development").strip().lower()
IS_PRODUCTION = WF_ENV == "production"

DEFAULT_DEV_KEYSTORE = BUILDER_ROOT / "keystore" / "test.keystore"
# SHA-256 of the PUBLIC dev certificate (CN=WFF Test, OU=Dev, O=WatchFace).
DEV_CERT_SHA256_COLONS = "61:24:82:4D:E0:7E:41:1E:E7:DB:86:51:71:22:89:3F:AD:0F:2C:EF:8F:FD:F7:BE:42:95:93:44:87:0C:8F:1B"

DEV_KEYSTORE_ALIAS = "wfftest"
DEV_KEYSTORE_PASS = "wfftest123"

KEYSTORE = Path(os.environ.get("WFF_KEYSTORE", str(DEFAULT_DEV_KEYSTORE)))
PRECOMPILED_DIR = BUILDER_ROOT / "projects" / "demo" / "_build" / "compiled"

# WFF 版本与 minSdk 映射
WFF_VERSION_MIN_SDK = {
    1: 33,   # Wear OS 4
    2: 34,   # Wear OS 5
    3: 34,
    4: 34,
}

ALIGNMENT = 4  # resources.arsc 对齐字节


# ─── 签名配置解析（审计 S1）──────────────────────────────

def _read_secret_from_env_or_file(name: str, file_name: str):
    """优先 env 变量；否则读文件内容（剥离首尾空白）。都不存在返回 None。"""
    val = os.environ.get(name)
    if val is not None and val != "":
        return val, "env"
    file_path = os.environ.get(file_name)
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip(), "file"
    return None, None


def _find_keytool() -> Optional[Path]:
    """定位 keytool: WFF_JAVA 同目录 > JAVA_HOME/bin > PATH。"""
    candidates = []
    wff_java = os.environ.get("WFF_JAVA")
    if wff_java:
        candidates.append(Path(wff_java).parent / "keytool")
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidates.append(Path(java_home) / "bin" / "keytool")
    which = shutil.which("keytool")
    if which:
        candidates.append(Path(which))
    for c in candidates:
        if c.is_file():
            return c
    return None


def _keystore_sha256(keystore: Path, pass_env_name: str, pass_file_var: str) -> str:
    """读取 keystore 第一个 key 的证书 SHA-256（冒号分隔大写十六进制）。

    密码经 keytool 的 -storepass:env / -storepass:file 引用传入，不落 argv 明文。
    """
    keytool = _find_keytool()
    if keytool is None:
        raise RuntimeError(
            "signing: keytool not found (set WFF_JAVA or JAVA_HOME); "
            "production builds require certificate fingerprint verification"
        )
    val, src = _read_secret_from_env_or_file(pass_env_name, pass_file_var)
    if src == "env":
        storepass_args = ["-storepass:env", pass_env_name]
    elif src == "file":
        storepass_args = ["-storepass:file", os.environ[pass_file_var]]
    else:
        storepass_args = ["-storepass:env", pass_env_name]  # 由调用方保证已存在
    r = subprocess.run(
        [str(keytool), "-list", "-v", "-keystore", str(keystore), *storepass_args],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError("signing: keystore unreadable (wrong password or format)")
    m = re.search(r"SHA256:\s*([0-9A-F:]+)", r.stdout)
    if not m:
        raise RuntimeError("signing: no certificate SHA256 found in keystore")
    return m.group(1).strip().upper()


class SigningConfig:
    """一次签名所需的全部参数（含 apksigner 密码引用形式）。"""

    def __init__(self, keystore: Path, alias: str, ks_pass_ref: str, key_pass_ref: str):
        self.keystore = keystore
        self.alias = alias
        self.ks_pass_ref = ks_pass_ref
        self.key_pass_ref = key_pass_ref


def _pass_ref(var_name: str, file_var_name: str, fallback_plain: str) -> str:
    """生成 apksigner --ks-pass/--key-pass 的引用参数（env:/file:/pass:）。"""
    val, src = _read_secret_from_env_or_file(var_name, file_var_name)
    if src == "env":
        return f"env:{var_name}"
    if src == "file":
        return f"file:{os.environ[file_var_name]}"
    return f"pass:{fallback_plain}"


def resolve_signing_config() -> SigningConfig:
    """按 WF_ENV 解析签名配置。每次构建调用（密码轮换无需重启）。

    development + 未显式配置 → 公开开发证书（pass: 引用，密码本就公开）。
    development + 显式 WFF_KEYSTORE → 自定义密钥库需配齐 alias/密码。
    production → 三件套强制 + 证书指纹不得等于公开开发证书。
    """
    keystore = Path(os.environ.get("WFF_KEYSTORE", str(DEFAULT_DEV_KEYSTORE)))
    alias = os.environ.get("WFF_KEYSTORE_ALIAS")
    store_val, store_src = _read_secret_from_env_or_file(
        "WFF_KEYSTORE_PASSWORD", "WFF_KEYSTORE_PASSWORD_FILE")
    explicit_ks = os.environ.get("WFF_KEYSTORE") is not None
    # 动态读取（模块加载后 env 变化也生效；测试可 monkeypatch）
    is_production = os.environ.get("WF_ENV", "development").strip().lower() == "production"

    if is_production:
        if not explicit_ks:
            raise RuntimeError(
                "signing: WF_ENV=production requires WFF_KEYSTORE "
                "(external keystore; the public dev keystore is not allowed)"
            )
        if not alias:
            raise RuntimeError("signing: WF_ENV=production requires WFF_KEYSTORE_ALIAS")
        if not store_val:
            raise RuntimeError(
                "signing: WF_ENV=production requires WFF_KEYSTORE_PASSWORD "
                "or WFF_KEYSTORE_PASSWORD_FILE"
            )
        # 证书级拒绝：换文件名也绕不过（指纹比对）
        fingerprint = _keystore_sha256(
            keystore, "WFF_KEYSTORE_PASSWORD", "WFF_KEYSTORE_PASSWORD_FILE")
        if fingerprint == DEV_CERT_SHA256_COLONS:
            raise RuntimeError(
                "signing: production build must not use the PUBLIC dev "
                "certificate (SHA256 match) — configure a private keystore"
            )
        return SigningConfig(
            keystore, alias,
            _pass_ref("WFF_KEYSTORE_PASSWORD", "WFF_KEYSTORE_PASSWORD_FILE", ""),
            _pass_ref("WFF_KEY_KEY_PASSWORD", "WFF_KEY_KEY_PASSWORD_FILE", store_val),
        )

    # development
    if explicit_ks and str(keystore.resolve()) != str(DEFAULT_DEV_KEYSTORE.resolve()):
        if not alias or not store_val:
            raise RuntimeError(
                "signing: custom WFF_KEYSTORE requires WFF_KEYSTORE_ALIAS and "
                "WFF_KEYSTORE_PASSWORD(_FILE)"
            )
        return SigningConfig(
            keystore, alias,
            _pass_ref("WFF_KEYSTORE_PASSWORD", "WFF_KEYSTORE_PASSWORD_FILE", ""),
            _pass_ref("WFF_KEY_KEY_PASSWORD", "WFF_KEY_KEY_PASSWORD_FILE", store_val),
        )
    # 开发默认: 公开证书（密码/alias 公开, 无泄露面）
    return SigningConfig(
        DEFAULT_DEV_KEYSTORE, DEV_KEYSTORE_ALIAS,
        f"pass:{DEV_KEYSTORE_PASS}", f"pass:{DEV_KEYSTORE_PASS}",
    )


def _scrub_apksigner_error(stderr: str) -> str:
    """apksigner 失败输出脱敏：去密码痕迹（防回显），保留可操作信息。"""
    cleaned = re.sub(r"(pass:)[^\s\"]+", r"\1***", stderr)
    return cleaned[:400]


# ─── 模板 ──────────────────────────────────────────────

MANIFEST_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools"
    package="{package_name}"
    android:versionCode="{version_code}"
    android:versionName="{version_name}">

    <uses-feature android:name="android.hardware.type.watch" />

    <uses-sdk
        android:minSdkVersion="{min_sdk}"
        android:targetSdkVersion="{target_sdk}" />

    <application
        android:label="@string/watch_face_name"
        android:hasCode="false"
        tools:ignore="MissingApplicationIcon">

        <meta-data
            android:name="com.google.android.wearable.standalone"
            android:value="true" />

        <property
            android:name="com.google.wear.watchface.format.version"
            android:value="{wff_version}" />

    </application>
</manifest>
"""

WATCH_FACE_INFO_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<WatchFaceInfo>
    <Preview value="@drawable/preview" />
    <Editable value="true" />
</WatchFaceInfo>
"""
# Editable=true: One UI 表盘编辑器「自定义」按钮的开关 (P2 根因, 2026-09-09 官方 sample 实证)
# 缺失时表盘可正常渲染/选择, 但编辑器不出现自定义入口

STRINGS_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="watch_face_name">{watch_face_name}</string>
</resources>
"""

PROJECT_YAML_TEMPLATE = """# WFF 表盘项目配置
package_name: com.example.mywatchface
version_code: 1
version_name: "1.0"
watch_face_name: My Watch Face
wff_version: 1              # WFF 版本 (1=Wear OS 4, 2+=Wear OS 5+)
# target_sdk: 33            # 可选，默认跟随 wff_version
# extra_drawables:          # 可选，额外图片资源
#   - background.png
# extra_fonts:              # 可选，额外字体资源
#   - custom_font.ttf
"""


# ─── WFF 规则校验引擎 ──────────────────────────────────

class WFFRule:
    """单条 WFF 规则，agent 可读、可执行、可验证。"""
    def __init__(self, rule_id: str, severity: str, check, fix: str, examples: dict = None):
        self.rule_id = rule_id
        self.severity = severity  # "error" | "warn"
        self.check = check        # callable(watchface_xml_text) -> (passed: bool, detail: str)
        self.fix = fix            # 修复说明
        self.examples = examples or {}  # {"bad": "...", "good": "..."}


def _check_rule_01(xml_text: str):
    """R01: WatchFace 根元素必须有 width 和 height 属性"""
    try:
        root = ET.fromstring(xml_text)
        w, h = root.get("width"), root.get("height")
        if not w or not h:
            return False, f"WatchFace 缺少 width/height 属性 (got width={w}, height={h})"
        return True, f"OK: {w}x{h}"
    except ET.ParseError as e:
        return False, f"XML 解析失败: {e}"


def _check_rule_02(xml_text: str):
    """R02: 必须有 Metadata CLOCK_TYPE"""
    if 'key="CLOCK_TYPE"' not in xml_text:
        return False, '缺少 <Metadata key="CLOCK_TYPE" value="DIGITAL|ANALOG"/>'
    return True, "OK"


def _check_rule_03(xml_text: str):
    """R03: 必须有 Metadata PREVIEW_TIME"""
    if 'key="PREVIEW_TIME"' not in xml_text:
        return False, '缺少 <Metadata key="PREVIEW_TIME" value="10:08:32"/>'
    return True, "OK"


def _check_rule_04(xml_text: str):
    """R04: Scene 应有 backgroundColor"""
    if "backgroundColor" not in xml_text:
        return False, 'Scene 缺少 backgroundColor, 建议添加 backgroundColor="#ff000000"'
    return True, "OK"


def _check_rule_05(xml_text: str):
    """R05: 表达式数据源必须用方括号包裹"""
    # 查找 expression="..." 中不含 [ ] 的纯标识符
    bad = re.findall(r'expression="([A-Z][A-Z0-9_]*)"', xml_text)
    if bad:
        return False, f'表达式缺少方括号: {bad} -> 应为 "[{bad[0]}]"'
    return True, "OK"


def _check_rule_06(xml_text: str):
    """R06: 不应有 clipShape 属性 (WFF v1 不支持)"""
    if "clipShape" in xml_text:
        return False, 'clipShape 在 WFF v1 不被支持, 请移除'
    return True, "OK"


def _check_rule_07(xml_text: str):
    """R07: Font family 应为 SYNC_TO_DEVICE, 不用 Roboto 等具体字体名"""
    bad_fonts = re.findall(r'family="(?!SYNC_TO_DEVICE)[A-Za-z ]+"', xml_text)
    if bad_fonts:
        return False, f'Font family 应为 "SYNC_TO_DEVICE", 发现: {bad_fonts}'
    return True, "OK"


def _check_rule_08(xml_text: str):
    """R08: 颜色格式应为 #ffRRGGBB (8位 ARGB)"""
    # 查找 #RRGGBB (6位) 而非 #AARRGGBB (8位)
    bad_colors = re.findall(r'color="#([0-9a-fA-F]{6})"', xml_text)
    if bad_colors:
        return False, f'颜色应为 8 位 ARGB 格式 (#ffRRGGBB), 发现 6 位: #{bad_colors[0]} -> #ff{bad_colors[0]}'
    return True, "OK"


def _check_rule_09(xml_text: str):
    """R09: DigitalClock 内部应使用 TimeText, 不用 Text+Template 显示时间"""
    # 简单检查: 如果有 DigitalClock 但没有 TimeText
    if "<DigitalClock" in xml_text and "<TimeText" not in xml_text:
        return False, "DigitalClock 内部应使用 TimeText 显示时间, 而非 Text+Template"
    return True, "OK"


def _check_rule_10(xml_text: str):
    """R10: 应有 ambient 模式 Variant"""
    if "<Variant" not in xml_text and "AMBIENT" not in xml_text:
        return False, "缺少 ambient 模式 Variant, 暗屏下表盘会全亮"
    return True, "OK"


def _check_rule_11(xml_text: str):
    """R11: 不应使用 source= 属性 (旧式写法, WFF 用 expression=)"""
    if re.search(r"\ssource\s*=", xml_text):
        return False, '使用 source="..." 是旧式写法, WFF 应使用 expression="[...]"'
    return True, "OK"


def _check_rule_12(xml_text: str):
    """R12: Parameter 必须用 expression= 属性, 不是 source="""
    if "<Parameter" in xml_text and re.search(r"\ssource\s*=", xml_text):
        return False, 'Parameter 应使用 expression="[...]" 而非 source="..."'
    return True, "OK"


# 已验证的 WFF 数据源表达式列表
WFF_DATA_SOURCES = {
    # XSD sourceType.xsd 全集（v5, 100 源, 2026-09-08 与官方枚举同步）
    "[HOUR_0_11]",
    "[HOUR_0_11_MINUTE]",
    "[HOUR_0_11_Z]",
    "[HOUR_0_23]",
    "[HOUR_0_23_MINUTE]",
    "[HOUR_0_23_Z]",
    "[HOUR_1_12]",
    "[HOUR_1_12_MINUTE]",
    "[HOUR_1_12_Z]",
    "[HOUR_1_24]",
    "[HOUR_1_24_MINUTE]",
    "[HOUR_1_24_Z]",
    "[MINUTE]",
    "[MINUTE_SECOND]",
    "[MINUTE_Z]",
    "[SECOND]",
    "[SECOND_MILLISECOND]",
    "[SECOND_Z]",
    "[MILLISECOND]",
    "[AMPM_POSITION]",
    "[AMPM_STATE]",
    "[AMPM_STRING]",
    "[AMPM_STRING_ENG]",
    "[AMPM_STRING_SHORT]",
    "[DAY]",
    "[DAY_0_30]",
    "[DAY_0_30_HOUR]",
    "[DAY_HOUR]",
    "[DAY_OF_WEEK]",
    "[DAY_OF_WEEK_F]",
    "[DAY_OF_WEEK_S]",
    "[DAY_OF_YEAR]",
    "[DAY_Z]",
    "[DAYS_IN_MONTH]",
    "[WEEK_IN_MONTH]",
    "[WEEK_IN_YEAR]",
    "[MONTH]",
    "[MONTH_0_11]",
    "[MONTH_0_11_DAY]",
    "[MONTH_DAY]",
    "[MONTH_F]",
    "[MONTH_S]",
    "[MONTH_Z]",
    "[YEAR]",
    "[YEAR_MONTH]",
    "[YEAR_MONTH_DAY]",
    "[YEAR_S]",
    "[TIMEZONE]",
    "[TIMEZONE_ABB]",
    "[TIMEZONE_ID]",
    "[TIMEZONE_OFFSET]",
    "[TIMEZONE_OFFSET_DST]",
    "[TIMEZONE_OFFSET_MINUTES]",
    "[TIMEZONE_OFFSET_MINUTES_DST]",
    "[UTC_TIMESTAMP]",
    "[SECONDS_IN_DAY]",
    "[SECONDS_SINCE_EPOCH]",
    "[MINUTES_SINCE_EPOCH]",
    "[HOURS_SINCE_EPOCH]",
    "[FIRST_DAY_OF_WEEK]",
    "[LANGUAGE_CODE]",
    "[LANGUAGE_COUNTRY_CODE]",
    "[LANGUAGE_LOCALE_NAME]",
    "[LANGUAGE_TEXT_DIRECTION]",
    "[BATTERY_CHARGING_STATUS]",
    "[BATTERY_IS_LOW]",
    "[BATTERY_PERCENT]",
    "[BATTERY_TEMPERATURE_CELSIUS]",
    "[BATTERY_TEMPERATURE_FAHRENHEIT]",
    "[STEP_COUNT]",
    "[STEP_GOAL]",
    "[STEP_PERCENT]",
    "[HEART_RATE]",
    "[HEART_RATE_Z]",
    "[ACCELEROMETER_ANGLE_X]",
    "[ACCELEROMETER_ANGLE_XY]",
    "[ACCELEROMETER_ANGLE_Y]",
    "[ACCELEROMETER_ANGLE_Z]",
    "[ACCELEROMETER_IS_SUPPORTED]",
    "[ACCELEROMETER_X]",
    "[ACCELEROMETER_Y]",
    "[ACCELEROMETER_Z]",
    "[WEATHER.CHANCE_OF_PRECIPITATION]",
    "[WEATHER.CONDITION]",
    "[WEATHER.CONDITION_NAME]",
    "[WEATHER.IS_AVAILABLE]",
    "[WEATHER.IS_DAY]",
    "[WEATHER.IS_ERROR]",
    "[WEATHER.LAST_UPDATED]",
    "[WEATHER.TEMPERATURE]",
    "[WEATHER.TEMPERATURE_HIGH]",
    "[WEATHER.TEMPERATURE_LOW]",
    "[WEATHER.TEMPERATURE_UNIT]",
    "[WEATHER.UV_INDEX]",
    "[MOON_PHASE_POSITION]",
    "[MOON_PHASE_TYPE]",
    "[MOON_PHASE_TYPE_STRING]",
    "[UNREAD_NOTIFICATION_COUNT]",
    "[IS_24_HOUR_MODE]",
    "[IS_DAYLIGHT_SAVING_TIME]",
    # 前缀引用型（点分路径）
    "[CONFIGURATION.",
    "[COMPLICATION.",
}

def _check_rule_13(xml_text: str):
    """R13: 表达式中的数据源应为已知名称"""
    # 提取所有 [...] 表达式
    bracket_exprs = re.findall(r'\[([A-Z][A-Z0-9_.]*)\]', xml_text)
    unknown = []
    for expr in bracket_exprs:
        full = f"[{expr}]"
        known = False
        for src in WFF_DATA_SOURCES:
            if full.startswith(src):
                known = True
                break
        if not known:
            unknown.append(full)
    if unknown:
        return False, f"未知数据源: {unknown}"
    return True, "OK"


def _check_rule_14(xml_text: str):
    """R14: Template 中 %s 格式化符数量应与 Parameter 数量匹配"""
    templates = re.findall(r'<Template>(.*?)</Template>', xml_text, re.DOTALL)
    for i, tpl in enumerate(templates):
        s_count = tpl.count("%s")
        params = re.findall(r'<Parameter', tpl)
        p_count = len(params)
        if s_count != p_count:
            return False, f"Template #{i+1}: {s_count} 个 %s 但 {p_count} 个 Parameter"
    return True, "OK"


def _check_rule_15(xml_text: str):
    """R15: 数字时间推荐用 DigitalClock+TimeText, 不用 PartText+Template"""
    if "<PartText" in xml_text and "SYSTEM_HOUR" in xml_text.upper():
        return False, "时间显示推荐用 DigitalClock+TimeText, 而非 PartText+Template"
    return True, "OK"


def _check_rule_16(xml_text: str):
    """R16: 不应使用已废弃的旧式 WatchFaceService 相关属性"""
    deprecated = ["WATCH_FACE", "BIND_WATCH_FACE", "watchface.wf"]
    for kw in deprecated:
        if kw in xml_text:
            return False, f"发现废弃属性: {kw} (WFF 不需要 WatchFaceService)"
    return True, "OK"


def _strip_xml_comments(xml_text: str) -> str:
    """剥离 XML 注释，避免注释中的示例文字误触发规则"""
    return re.sub(r'<!--.*?-->', '', xml_text, flags=re.DOTALL)


def _check_rule_26(xml_text: str):
    """R26: 空 Complication 真机渲染为空（BT-03 真机实证 2026-08-31）

    <Complication type="..."/> 不含 Part 组件时，XSD 合法但设备上什么都不画。
    必须内部放 PartText/PartImage/PartDraw + [COMPLICATION.*] 数据绑定。
    """
    xml_text = _strip_xml_comments(xml_text)
    # 自闭合或开闭标签之间无 Part 元素
    for m in re.finditer(r'<Complication\b[^>]*?/>', xml_text):
        return False, f"空 <Complication .../> 真机渲染为空 (行内无渲染组件): {m.group(0)[:80]}"
    for m in re.finditer(r'<Complication\b[^>]*>(.*?)</Complication>', xml_text, re.DOTALL):
        inner = m.group(1)
        if '<Part' not in inner and '<Group' not in inner and '<Condition' not in inner:
            return False, "Complication 内无 PartText/PartImage/PartDraw 渲染组件, 真机渲染为空"
    # ComplicationSlot 存在时应有 [COMPLICATION.*] 数据绑定
    if "<ComplicationSlot" in xml_text and "[COMPLICATION." not in xml_text:
        return False, "检测到 ComplicationSlot 但未发现 [COMPLICATION.*] 数据绑定表达式"
    return True, "OK"


def _check_rule_27(xml_text: str):
    """R27: 矢量 RoundRectangle 用 cornerRadiusX/cornerRadiusY（真机实证 2026-08-31）

    单一 cornerRadius 是 BoundingRoundBox 的属性；矢量 <RoundRectangle> 只接受
    cornerRadiusX + cornerRadiusY（均必填）。
    """
    xml_text = _strip_xml_comments(xml_text)
    for m in re.finditer(r'<RoundRectangle\b[^>]*>', xml_text):
        tag = m.group(0)
        if 'cornerRadius=' in tag or 'cornerRadiusX' not in tag or 'cornerRadiusY' not in tag:
            return False, f"矢量 RoundRectangle 需 cornerRadiusX + cornerRadiusY (无单一 cornerRadius): {tag[:80]}"
    return True, "OK"


def _check_rule_32(xml_text: str):
    """R32: Condition 结构三查（XSD 实证 2026-09-07，官方 conditionElement.xsd）

    1) <Condition expression="..."> 属性不存在（旧知识层错误写法）
    2) <Condition> 必须含 <Expressions><Expression name="...">算式</Expression>
    3) <Compare expression="..."> 是对 Expression/@name 的引用（keyref）
    另: 运算符无 < <=（XML 非法字符），"低于X" 写成 X > [SRC]
    """
    xml_text = _strip_xml_comments(xml_text)
    if "<Condition" not in xml_text:
        return True, "OK"
    for m in re.finditer(r'<Condition\b[^>]*\bexpression\s*=', xml_text):
        return False, f"Condition 无 expression 属性 (算式在 Expressions/Expression 文本, R32): {m.group(0)[:80]}"
    for m in re.finditer(r'<Condition\b[^>]*>(.*?)</Condition>', xml_text, re.DOTALL):
        inner = m.group(1)
        if '<Expressions>' not in inner or '<Expression' not in inner:
            return False, "Condition 内缺 <Expressions><Expression name=...> (R32, XSD 必填)"
        names = set(re.findall(r'<Expression\b[^>]*\bname\s*=\s*"([^"]+)"', inner))
        for cm in re.finditer(r'<Compare\b[^>]*\bexpression\s*=\s*"([^"]+)"', inner):
            if cm.group(1).strip() not in names:
                return False, f"Compare expression=\"{cm.group(1)}\" 未在 Expressions 中定义 (R32 keyref)"
    for m in re.finditer(r'\[[A-Z_0-9]+\]\s*<\s*[0-9]', xml_text):
        return False, f"表达式无 < 运算符 (反转写: 20 > [SRC], R32): {m.group(0)[:60]}"
    return True, "OK"


def _check_rule_34(xml_text: str):
    """R34: 圆形表盘溢出检查（真机实证 2026-09-10，P2 拱顶被切数像素）

    圆屏只显示画布的内切圆。顶层元素 bbox 的四角到画布中心距离 > 半径，
    该角即被屏幕切掉。顶部/底部窄条元素尤其高危（内切圆在竖直方向亏欠最多）。
    """
    xml_text = _strip_xml_comments(xml_text)
    wm = re.search(r'<WatchFace\b[^>]*\bwidth="([\d.]+)"', xml_text)
    hm = re.search(r'<WatchFace\b[^>]*\bheight="([\d.]+)"', xml_text)
    if not (wm and hm):
        return True, "OK"
    W, H = float(wm.group(1)), float(hm.group(1))
    cx, cy, R = W / 2, H / 2, min(W, H) / 2
    # Scene 直接子元素 (全局坐标)
    scene = re.search(r'<Scene\b[^>]*>(.*)</Scene>', xml_text, re.DOTALL)
    if not scene:
        return True, "OK"
    scene_body = scene.group(1)
    # 剥离嵌套块 (其内部是局部坐标系, 不做全局内切圆检查):
    # ComplicationSlot/Complication 的子元素、List/Boolean 渲染版 Option 内容 (BT-08 反馈 #3)
    scene_body = re.sub(r'<ComplicationSlot\b[^>]*(/>|>.*?</ComplicationSlot>)', '', scene_body, flags=re.DOTALL)
    scene_body = re.sub(r'<ListConfiguration\b[^>]*(/>|>.*?</ListConfiguration>)', '', scene_body, flags=re.DOTALL)
    scene_body = re.sub(r'<BooleanConfiguration\b[^>]*(/>|>.*?</BooleanConfiguration>)', '', scene_body, flags=re.DOTALL)
    scene_body = re.sub(r'<AnalogClock\b[^>]*(/>|>.*?</AnalogClock>)|<DigitalClock\b[^>]*(/>|>.*?</DigitalClock>)', '', scene_body, flags=re.DOTALL)
    for m in re.finditer(r'<(PartDraw|PartText|PartImage|Group)\b([^>]*?)(/>|>)',
                         scene_body):
        attrs = m.group(2)
        x = re.search(r'\bx="(-?[\d.]+)"', attrs)
        y = re.search(r'\by="(-?[\d.]+)"', attrs)
        w = re.search(r'\bwidth="([\d.]+)"', attrs)
        h = re.search(r'\bheight="([\d.]+)"', attrs)
        if not all([x, y, w, h]):
            continue
        x0, y0 = float(x.group(1)), float(y.group(1))
        x1, y1 = x0 + float(w.group(1)), y0 + float(h.group(1))
        # 全画布容器是常见合法 pattern (内容实际居中/有内边距), 跳过
        if x0 <= 5 and y0 <= 5 and x1 >= W - 5 and y1 >= H - 5:
            continue
        # 四角到中心最大距离
        dmax = max(math.hypot(px - cx, py - cy)
                   for px in (x0, x1) for py in (y0, y1))
        if dmax > R + 0.5:
            overflow = dmax - R
            return False, (f"<{m.group(1)}> ({x0:.0f},{y0:.0f} {w.group(1)}x{h.group(1)}) "
                           f"bbox 角超出内切圆 {overflow:.0f}px, 圆屏边缘会切掉 (R34); "
                           f"参考: 内切圆中心({cx:.0f},{cy:.0f}) 半径{R:.0f}, "
                           f"顶部元素 y≥{cy - R:.0f}+安全边距, 或收窄宽度")
    return True, "OK"


def _check_rule_35(xml_text: str):
    """R35: Arc 椭圆 bbox 溢出父 PartDraw 容器（真机实证 2026-09-10 斜线悬案）

    Arc 的 centerX/centerY 是 PartDraw **局部坐标**。椭圆中心偏离容器中心时，
    溢出容器的弧段被直接裁剪——表现为"斜线"/"半段弧"。
    检测：每对 (PartDraw 容器 w/h, 内部 Arc bbox) 比对。
    """
    xml_text = _strip_xml_comments(xml_text)
    for m in re.finditer(
            r'<PartDraw\b([^>]*?)(/>|>(.*?)</PartDraw>)', xml_text, re.DOTALL):
        attrs = m.group(1)
        body = m.group(3) or ""
        cw = re.search(r'\bwidth="([\d.]+)"', attrs)
        ch = re.search(r'\bheight="([\d.]+)"', attrs)
        if not (cw and ch) or "<Arc" not in body:
            continue
        CW, CH = float(cw.group(1)), float(ch.group(1))
        for am in re.finditer(r'<Arc\b([^>]*)>', body):
            aa = am.group(1)
            ax = re.search(r'\bcenterX="(-?[\d.]+)"', aa)
            ay = re.search(r'\bcenterY="(-?[\d.]+)"', aa)
            aw = re.search(r'\bwidth="([\d.]+)"', aa)
            ah = re.search(r'\bheight="([\d.]+)"', aa)
            if not all([ax, ay, aw, ah]):
                continue
            ex0 = float(ax.group(1)) - float(aw.group(1)) / 2
            ey0 = float(ay.group(1)) - float(ah.group(1)) / 2
            ex1 = float(ax.group(1)) + float(aw.group(1)) / 2
            ey1 = float(ay.group(1)) + float(ah.group(1)) / 2
            if ex0 < -0.5 or ey0 < -0.5 or ex1 > CW + 0.5 or ey1 > CH + 0.5:
                return False, (f"Arc 椭圆 bbox ({ex0:.0f},{ey0:.0f})-({ex1:.0f},{ey1:.0f}) "
                               f"溢出 PartDraw 容器 {CW:.0f}x{CH:.0f}, 溢出段被裁剪 (R35 斜线悬案); "
                               f"centerX/centerY 是局部坐标, 居中应写: centerX={CW/2:.0f} centerY={CH/2:.0f}")
    return True, "OK"


def _check_rule_37(xml_text: str):
    """R37: List/Boolean 配置 id 两边对应（XSD 引用链 + Flavors sample 实证 2026-09-10）

    容器版（UserConfigurations 内）定义选项列表；渲染版（Scene/Group 内）按 id
    匹配选项渲染内容。渲染版的 ListOption id 必须在容器版中定义；
    渲染版 BooleanConfiguration 的 id 也应在容器版存在（否则编辑器无此开关）。
    """
    xml_text = _strip_xml_comments(xml_text)
    uc = re.search(r'<UserConfigurations>(.*?)</UserConfigurations>', xml_text, re.DOTALL)
    uc_text = uc.group(1) if uc else ""
    # 容器版各配置 id → ListOption ids
    container = {}
    for m in re.finditer(r'<ListConfiguration\b([^>]*?)(?:/>|>(.*?)</ListConfiguration>)', uc_text, re.DOTALL):
        cid = re.search(r'\bid="([^"]+)"', m.group(1))
        if cid:
            opts = set(re.findall(r'<ListOption\b[^>]*\bid="([^"]+)"', m.group(2) or ""))
            container[cid.group(1)] = opts
    bool_ids = set(re.findall(r'<BooleanConfiguration\b[^>]*\bid="([^"]+)"', uc_text))
    list_ids = set(container.keys())
    # 渲染版: UserConfigurations 之外的部分
    body = xml_text.replace(uc.group(0), '') if uc else xml_text
    for m in re.finditer(r'<ListConfiguration\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</ListConfiguration>', body, re.DOTALL):
        rid, inner = m.group(1), m.group(2)
        if rid not in list_ids:
            return False, (f"渲染版 ListConfiguration id=\"{rid}\" 未在 UserConfigurations 容器版定义 (R37); "
                           f"容器版已有: {sorted(list_ids) or '无'}")
        for oid in re.findall(r'<ListOption\b[^>]*\bid="([^"]+)"', inner):
            if oid not in container[rid]:
                return False, (f"渲染版 ListOption id=\"{oid}\" 不在容器版 ListConfiguration \"{rid}\" 的选项集 {sorted(container[rid])} 内 (R37)")
    for m in re.finditer(r'<BooleanConfiguration\b[^>]*\bid="([^"]+)"[^>]*>\s*<BooleanOption', body):
        bid = m.group(1)
        if bid not in bool_ids:
            return False, (f"渲染版 BooleanConfiguration id=\"{bid}\" 未在 UserConfigurations 容器版定义 (R37); "
                           "容器版缺此开关则编辑器无法控制该渲染块")
    # 渲染版 BooleanOption id 只能 TRUE/FALSE
    for m in re.finditer(r'<BooleanOption\b[^>]*\bid="([^"]+)"', body):
        if m.group(1) not in ("TRUE", "FALSE"):
            return False, f"BooleanOption id=\"{m.group(1)}\" 非法 (R37): 只能 TRUE 或 FALSE"
    return True, "OK"


def _check_rule_38(xml_text: str):
    """R38: ComplicationSlot 上限 8、slotId 全局唯一（sceneElement.xsd maxOccurs=8 + xs:unique）

    slotId 官方 samples 从 0 开始（类型 xs:string 无数值约束）。
    """
    xml_text = _strip_xml_comments(xml_text)
    slots = re.findall(r'<ComplicationSlot\b[^>]*>', xml_text)
    if len(slots) > 8:
        return False, f"ComplicationSlot 数量 {len(slots)} 超上限 8 (R38, sceneElement.xsd maxOccurs)"
    ids = []
    for s in slots:
        m = re.search(r'\bslotId="([^"]+)"', s)
        if m:
            ids.append(m.group(1))
    dups = [i for i in set(ids) if ids.count(i) > 1]
    if dups:
        return False, f"slotId 重复: {sorted(dups)} (R38, XSD xs:unique 强制全局唯一)"
    return True, "OK"


def _check_rule_39(xml_text: str):
    """R39: PartText 文本三层结构 PartText > Text > Font（XSD v1/v5 一致，validator 强制）

    Font 直挂 PartText：渲染器可能宽容，但 wff-validator 拒绝（v0.4.0 预审实证）。
    检测：PartText 直接子元素中出现 <Font（无 <Text> 包装）。
    """
    xml_text = _strip_xml_comments(xml_text)
    for m in re.finditer(r'<PartText\b[^>]*>(.*?)</PartText>', xml_text, re.DOTALL):
        inner = m.group(1)
        has_font = re.search(r'<Font\b', inner)
        has_text = re.search(r'<Text\b', inner)
        if has_font and not has_text:
            # Font 前没有 Text 包装 → 报错 (Font 可能在 Outline 内部, 但那也在 Text 内)
            return False, ("PartText 直接含 <Font> 缺 <Text> 包装层 (R39): "
                           "PartText > Text > Font 三层结构, wff-validator 强制; "
                           "参考: <PartText ...><Text align=\"CENTER\"><Font ...>...</Font></Text></PartText>")
    return True, "OK"


def _check_rule_28(xml_text: str):
    """R28: BoundingShape 用 slot 局部坐标（真机实证 2026-08-31 第二轮）

    官方示例 slot x=100 y=100 的 BoundingOval 写 x=0 y=0——边界坐标系是 slot
    左上角原点。把 slot 全局坐标抄进 BoundingShape 会让槽位落到画布外：
    不渲染 + 编辑器无自定义入口。
    检测：BoundingShape 的 x/y 或 x+width/y+height 明显超出 slot 自身宽高。
    """
    xml_text = _strip_xml_comments(xml_text)
    for m in re.finditer(
            r'<ComplicationSlot\b([^>]*)>(.*?)</ComplicationSlot>', xml_text, re.DOTALL):
        slot_attrs, inner = m.group(1), m.group(2)
        sw = re.search(r'width="([\d.]+)"', slot_attrs)
        sh = re.search(r'height="([\d.]+)"', slot_attrs)
        if not (sw and sh):
            continue
        slot_w, slot_h = float(sw.group(1)), float(sh.group(1))
        bm = re.search(r'<Bounding\w+\b([^>]*)/>', inner)
        if not bm:
            continue
        b_attrs = bm.group(1)
        bx = re.search(r'\bx="(-?[\d.]+)"', b_attrs)
        by = re.search(r'\by="(-?[\d.]+)"', b_attrs)
        bw = re.search(r'width="([\d.]+)"', b_attrs)
        bh = re.search(r'height="([\d.]+)"', b_attrs)
        if not all([bx, by, bw, bh]):
            continue
        bxv, byv, bwv, bhv = (float(g.group(1)) for g in [bx, by, bw, bh])
        # 允许 50% 余量（outlinePadding 等），超出视为全局坐标误写
        if bxv > slot_w * 1.5 or byv > slot_h * 1.5 or \
           bxv + bwv > slot_w * 1.5 or byv + bhv > slot_h * 1.5:
            return False, (f"BoundingShape 疑似用了全局坐标 (x={bxv},y={byv} 超出 slot "
                           f"{slot_w}x{slot_h})——应使用 slot 局部坐标 (0,0 起)")
    return True, "OK"


def _check_rule_29(xml_text: str):
    """R29: Template 至少含一个 Parameter（XSD 强制）；静态文本直接放 Font"""
    xml_text = _strip_xml_comments(xml_text)
    for m in re.finditer(r'<Template>(.*?)</Template>', xml_text, re.DOTALL):
        inner = m.group(1)
        if '<Parameter' not in inner:
            return False, "Template 必须至少含一个 <Parameter> (XSD 强制); 静态文本直接写 <Font>text</Font>"
    return True, "OK"


# 规则注册表
WFF_RULES = [
    WFFRule("R01", "error", _check_rule_01,
        "WatchFace 根元素必须有 width 和 height 属性",
        {"good": '<WatchFace width="450" height="450">'}),
    WFFRule("R02", "error", _check_rule_02,
        '添加 <Metadata key="CLOCK_TYPE" value="DIGITAL"/> 或 ANALOG',
        {"good": '<Metadata key="CLOCK_TYPE" value="DIGITAL"/>'}),
    WFFRule("R03", "error", _check_rule_03,
        '添加 <Metadata key="PREVIEW_TIME" value="10:08:32"/>',
        {"good": '<Metadata key="PREVIEW_TIME" value="10:08:32"/>'}),
    WFFRule("R04", "warn", _check_rule_04,
        '在 Scene 上添加 backgroundColor="#ff000000"',
        {"good": '<Scene backgroundColor="#ff000000">'}),
    WFFRule("R05", "error", _check_rule_05,
        "数据源表达式必须用方括号包裹: expression=\"[MONTH]\" 不是 expression=\"MONTH\"",
        {"bad": 'expression="MONTH"', "good": 'expression="[MONTH]"'}),
    WFFRule("R06", "error", _check_rule_06,
        "移除 clipShape 属性, WFF v1 不支持",
        {"bad": '<WatchFace ... clipShape="CIRCLE">', "good": '<WatchFace width="450" height="450">'}),
    WFFRule("R07", "warn", _check_rule_07,
        "Font family 应为 SYNC_TO_DEVICE",
        {"bad": 'family="Roboto"', "good": 'family="SYNC_TO_DEVICE"'}),
    WFFRule("R08", "error", _check_rule_08,
        "颜色用 8 位 ARGB 格式: #ffRRGGBB (不是 #RRGGBB)",
        {"bad": 'color="#00F5FF"', "good": 'color="#ff00F5FF"'}),
    WFFRule("R09", "error", _check_rule_09,
        "时间用 DigitalClock+TimeText, 不用 Text+Template",
        {"bad": '<Text>...<Template>%s:%s<Parameter expression="[HOUR]"/></Template>',
         "good": '<DigitalClock><TimeText format="hh:mm">...</TimeText></DigitalClock>'}),
    WFFRule("R10", "warn", _check_rule_10,
        "添加 ambient 模式 Variant, 暗屏下降低功耗",
        {"good": '<Variant mode="AMBIENT" target="alpha" value="0"/>'}),
    WFFRule("R11", "error", _check_rule_11,
        "使用 expression=\"[...]\" 替代 source=\"...\"",
        {"bad": '<Parameter source="SYSTEM_HOUR"/>', "good": '<Parameter expression="[HOUR_0_23]"/>'}),
    WFFRule("R12", "error", _check_rule_12,
        "Parameter 必须用 expression= 属性",
        {"bad": '<Parameter source="MONTH"/>', "good": '<Parameter expression="[MONTH]"/>'}),
    WFFRule("R13", "warn", _check_rule_13,
        "使用已验证的数据源名称, 查阅 WFF_DATA_SOURCES 列表"),
    WFFRule("R14", "error", _check_rule_14,
        "Template 中 %s 数量必须与 Parameter 数量一致"),
    WFFRule("R15", "warn", _check_rule_15,
        "数字时间用 DigitalClock+TimeText 而非 PartText+Template"),
    WFFRule("R16", "error", _check_rule_16,
        "WFF 不需要 WatchFaceService 相关声明"),
    WFFRule("R26", "error", _check_rule_26,
        "空 Complication 真机渲染为空; 内部放 PartText/PartImage + [COMPLICATION.*] 绑定",
        {"bad": '<Complication type="SHORT_TEXT"/>',
         "good": '<Complication type="SHORT_TEXT"><PartText ...><Template>%s<Parameter expression="[COMPLICATION.TEXT]"/></Template>...</PartText></Complication>'}),
    WFFRule("R27", "error", _check_rule_27,
        "矢量 RoundRectangle 需 cornerRadiusX + cornerRadiusY",
        {"bad": '<RoundRectangle ... cornerRadius="14"/>',
         "good": '<RoundRectangle ... cornerRadiusX="14" cornerRadiusY="14"/>'}),
    WFFRule("R28", "error", _check_rule_28,
        "BoundingShape 用 slot 局部坐标 (0,0 起), 写全局坐标槽位整体消失",
        {"bad": '<ComplicationSlot x="140" y="328" ...><BoundingRoundBox x="140" y="328" .../>',
         "good": '<ComplicationSlot x="140" y="328" ...><BoundingRoundBox x="0" y="0" .../>'}),
    WFFRule("R29", "error", _check_rule_29,
        "Template 至少含一个 Parameter; 静态文本直接写 <Font>text</Font>",
        {"bad": '<Template>--</Template>',
         "good": '<Font family="SYNC_TO_DEVICE" size="24">--</Font>'}),
    WFFRule("R32", "error", _check_rule_32,
        "Condition: 算式在 Expressions/Expression 文本, Compare 按 name 引用; 无 < 运算符",
        {"bad": '<Condition expression="[BATTERY_PERCENT] < 20"><Compare expression="1">',
         "good": '<Condition><Expressions><Expression name="low">20 > [BATTERY_PERCENT]</Expression></Expressions><Compare expression="low">'}),
    WFFRule("R34", "warn", _check_rule_34,
        "圆屏只显示画布内切圆: 顶层元素 bbox 角超出内切圆会被屏幕切掉",
        {"bad": '<PartDraw x="0" y="0" width="450" height="80">  <!-- 顶部窄条四角全在外 -->',
         "good": '<PartDraw x="105" y="12" width="240" height="72">  <!-- 角点距离中心 ≤ 半径 -->'}),
    WFFRule("R35", "warn", _check_rule_35,
        "Arc centerX/centerY 是 PartDraw 局部坐标: 椭圆溢出容器被裁, 弧线变斜线",
        {"bad": '<PartDraw width="320" height="44"><Arc centerX="225" ... width="320" ...>',
         "good": '<PartDraw width="320" height="44"><Arc centerX="160" centerY="22" width="320" height="44" ...>'}),
    WFFRule("R37", "error", _check_rule_37,
        "List/Boolean 渲染版 id 必须与容器版对应; BooleanOption id 只能 TRUE/FALSE",
        {"bad": '<ListConfiguration id="style"><ListOption id="9">…</ListOption>…(容器版无 id=9)',
         "good": '容器版 <ListConfiguration id="style"><ListOption id="0"/><ListOption id="1"/> + 渲染版 ListOption id 只用 0/1'}),
    WFFRule("R38", "error", _check_rule_38,
        "ComplicationSlot 上限 8 个, slotId 全局唯一 (官方从 0 起)",
        {"bad": '9 个 ComplicationSlot 或 slotId="1" 重复',
         "good": '≤8 个槽, slotId 各不相同'}),
    WFFRule("R39", "error", _check_rule_39,
        "PartText > Text > Font 三层结构, Font 直挂 PartText 被 validator 拒",
        {"bad": '<PartText ...><Font family="SYNC_TO_DEVICE" ...>text</Font></PartText>',
         "good": '<PartText ...><Text align="CENTER"><Font family="SYNC_TO_DEVICE" ...>text</Font></Text></PartText>'}),
]


def check_watch_face_info(project_dir: str):
    """R33 (项目级): res/xml/watch_face_info.xml 必须存在且含 <Editable value="true"/>

    One UI 表盘编辑器「自定义」按钮的总开关 (P2 根因, 2026-09-09 四轮单变量迭代实证;
    官方 samples: android/wear-os-samples/WatchFaceFormat)。缺失时表盘渲染/选择/安装
    全正常, 仅编辑器不出现自定义入口——所有 UserConfigurations 相关修复都救不了它。
    返回 (passed, detail)。
    """
    info_path = Path(project_dir) / "res" / "xml" / "watch_face_info.xml"
    if not info_path.exists():
        return False, ("res/xml/watch_face_info.xml 不存在 (R33): 编辑器自定义按钮的开关文件; "
                       "builder build 会自动生成 (模板已含 Editable), 手写项目必须自带")
    text = _strip_xml_comments(info_path.read_text(encoding="utf-8"))
    if not re.search(r'<Editable\b[^>]*\bvalue\s*=\s*"true"', text):
        return False, ('watch_face_info.xml 缺 <Editable value="true"/> (R33): '
                       'One UI 编辑器自定义按钮总开关, 缺失则 UserConfigurations 不显示入口')
    return True, "OK"


def validate_watchface_xml(xml_text: str, verbose=False) -> list:
    """校验 watchface.xml, 返回失败规则列表"""
    failures = []
    for rule in WFF_RULES:
        passed, detail = rule.check(xml_text)
        status = "PASS" if passed else ("FAIL" if rule.severity == "error" else "WARN")
        if not passed:
            failures.append({
                "rule_id": rule.rule_id,
                "severity": rule.severity,
                "detail": detail,
                "fix": rule.fix,
                "examples": rule.examples,
            })
        if verbose:
            print(f"  [{status}] {rule.rule_id}: {detail}")
    return failures


# ─── 核心构建逻辑 ──────────────────────────────────────

class WFFBuilder:
    def __init__(self, project_dir: str, verbose: bool = True):
        self.project_dir = Path(project_dir).resolve()
        self.verbose = verbose
        self.config = {}
        self.build_dir = self.project_dir / "_build"
        self.compiled_dir = self.build_dir / "compiled"

    def log(self, msg: str):
        if self.verbose:
            print(msg)

    def load_config(self) -> dict:
        config_path = self.project_dir / "project.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"project.yaml not found in {self.project_dir}")

        import re
        config = {}
        text = config_path.read_text()
        # 列表支持（真机盲测 Round 2 反馈 2026-09-06）：extra_drawables 等列表项
        # 此前被逐行 key:value 正则静默忽略 → drawable 不进包
        current_list_key = None
        for line in text.splitlines():
            raw = line
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # 列表项 "  - item"
            lm = re.match(r"^-\s+(.+)$", line)
            if lm and current_list_key:
                item = lm.group(1).strip().strip('"')
                if isinstance(config.get(current_list_key), list):
                    config[current_list_key].append(item)
                continue
            m = re.match(r"^(\w+):\s*(.*)$", line)
            if not m:
                continue
            key, val = m.group(1), m.group(2).strip()
            if not val:
                # 可能是列表头（下一行起 "  - item"）
                current_list_key = key
                config[key] = []
                continue
            current_list_key = None
            # 行内列表 [a, b] 或 key: - a（罕见单行）
            if val.startswith("[") and val.endswith("]"):
                config[key] = [v.strip().strip('"') for v in val[1:-1].split(",") if v.strip()]
                continue
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.isdigit():
                val = int(val)
            config[key] = val
        # 清掉误判为列表的空标量（例如空行注释块）
        self.config = config

        wff_ver = config.get("wff_version", 1)
        min_sdk = config.get("min_sdk") or WFF_VERSION_MIN_SDK.get(wff_ver, 33)
        target_sdk = config.get("target_sdk", min_sdk)
        config["min_sdk"] = min_sdk
        config["target_sdk"] = target_sdk
        return config

    def generate_manifest(self):
        config = self.config
        manifest = MANIFEST_TEMPLATE.format(
            package_name=config["package_name"],
            version_code=config["version_code"],
            version_name=config["version_name"],
            min_sdk=config["min_sdk"],
            target_sdk=config["target_sdk"],
            wff_version=config["wff_version"],
        )
        manifest_path = self.build_dir / "AndroidManifest.xml"
        manifest_path.write_text(manifest)
        self.log(f"  Generated: AndroidManifest.xml (WFF v{config['wff_version']}, minSdk={config['min_sdk']})")

    def generate_resource_files(self):
        # watch_face_info.xml
        info_path = self.build_dir / "res" / "xml" / "watch_face_info.xml"
        info_path.parent.mkdir(parents=True, exist_ok=True)
        info_path.write_text(WATCH_FACE_INFO_TEMPLATE)
        self.log("  Generated: res/xml/watch_face_info.xml")

        # strings.xml: 模板生成 watch_face_name + 合并项目自带 res/values/strings.xml
        strings_path = self.build_dir / "res" / "values" / "strings.xml"
        strings_path.parent.mkdir(parents=True, exist_ok=True)
        strings_xml = STRINGS_TEMPLATE.format(
            watch_face_name=self.config["watch_face_name"]
        )
        # 项目级 strings.xml：displayName 等编辑器资源用裸资源名引用 (WFF 库按名自查 arsc,
        # res/raw XML 不经 aapt2 编译, @string/ 前缀是字面量会查不到; 官方 sample 实证 2026-09-09)
        project_strings = self.project_dir / "res" / "values" / "strings.xml"
        if project_strings.is_file():
            extra = project_strings.read_text(encoding="utf-8")
            extra_items = re.findall(r'<string\b[^>]*>.*?</string>', extra, re.DOTALL)
            if extra_items:
                strings_xml = strings_xml.replace(
                    "</resources>",
                    "\n    " + "\n    ".join(extra_items) + "\n</resources>")
                self.log(f"  Merged: project res/values/strings.xml ({len(extra_items)} entries)")
        strings_path.write_text(strings_xml, encoding="utf-8")
        self.log(f"  Generated: res/values/strings.xml (name='{self.config['watch_face_name']}')")

        # Copy watchface.xml
        wf_src = self.project_dir / "watchface.xml"
        if not wf_src.exists():
            raise FileNotFoundError(f"watchface.xml not found in {self.project_dir}")
        wf_dst = self.build_dir / "res" / "raw" / "watchface.xml"
        wf_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(wf_src, wf_dst)
        self.log(f"  Copied: res/raw/watchface.xml ({wf_dst.stat().st_size}B)")

        # Copy preview.png
        preview_src = self.project_dir / "preview.png"
        if not preview_src.exists():
            raise FileNotFoundError(f"preview.png not found in {self.project_dir}")
        preview_dst = self.build_dir / "res" / "drawable" / "preview.png"
        preview_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(preview_src, preview_dst)
        self.log(f"  Copied: res/drawable/preview.png ({preview_dst.stat().st_size}B)")

        # Copy extra drawables
        # API 构建链路的标准背景资源（无需 project.yaml 列表解析）
        background_src = self.project_dir / "background.png"
        if background_src.is_file():
            background_dst = self.build_dir / "res" / "drawable" / "background.png"
            background_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(background_src, background_dst)
            self.log("  Copied: res/drawable/background.png")

        for drawable in self.config.get("extra_drawables", []):
            if isinstance(drawable, str):
                src = self.project_dir / drawable
                if src.exists():
                    dst = self.build_dir / "res" / "drawable" / src.name
                    shutil.copy2(src, dst)
                    self.log(f"  Copied: res/drawable/{src.name}")

        # 项目级 res/drawable/*.png 自动打包（盲测 Round 2 反馈 2026-09-06）：
        # 与 res/values/strings.xml 自动合并同约定——agent 直觉是把素材放
        # project/res/drawable/，无需在 project.yaml 里重复列清单
        project_drawables = self.project_dir / "res" / "drawable"
        if project_drawables.is_dir():
            for src in sorted(project_drawables.glob("*.png")):
                dst = self.build_dir / "res" / "drawable" / src.name
                # 始终覆盖（2026-09-15 真机踩坑：旧逻辑"目标存在就跳过"导致
                # 项目资源更新后不进包，图标连续 4 轮未生效）
                shutil.copy2(src, dst)
                self.log(f"  Auto-packed: res/drawable/{src.name}")

            # 清理项目已删除的 stale 资源（builder 自产文件除外）
            keep = {p.name for p in project_drawables.glob("*.png")}
            keep.update({"background.png", "preview.png"})
            for old in (self.build_dir / "res" / "drawable").glob("*.png"):
                if old.name not in keep:
                    old.unlink()
                    self.log(f"  Removed stale: res/drawable/{old.name}")

        # Copy extra fonts
        for font in self.config.get("extra_fonts", []):
            if isinstance(font, str):
                src = self.project_dir / font
                if src.exists():
                    dst = self.build_dir / "res" / "font" / src.name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    self.log(f"  Copied: res/font/{src.name}")

    def compile_resources(self):
        # aapt2 官方 Linux 构建不支持当前 ARM64 DevSpace。使用仓库内
        # 已验证的二进制模板，仅替换 WFF 原始 XML 和预览图资源。
        if not (AAPT2.is_file() and os.access(AAPT2, os.X_OK) and ANDROID_JAR.is_file()):
            required = [
                "AndroidManifest.xml",
                "resources.arsc",
                "res_xml_watch_face_info.xml",
            ]
            missing = [name for name in required if not (PRECOMPILED_DIR / name).is_file()]
            if missing:
                raise RuntimeError(
                    "Android build tools are unavailable and the precompiled template is incomplete: "
                    + ", ".join(missing)
                )
            if self.compiled_dir.exists():
                shutil.rmtree(self.compiled_dir)
            shutil.copytree(PRECOMPILED_DIR, self.compiled_dir)
            background = self.build_dir / "res" / "drawable" / "background.png"
            if background.is_file():
                # 预编译 resources.arsc 只注册了 drawable/preview。ARM 回退时
                # 将背景映射到该已注册槽位，避免 APK 内有文件但资源无法解析。
                watchface = (self.build_dir / "res" / "raw" / "watchface.xml").read_text()
                watchface = watchface.replace('resource="drawable/background"', 'resource="drawable/preview"')
                (self.compiled_dir / "res_raw_watchface.xml").write_text(watchface)
                shutil.copy2(background, self.compiled_dir / "res_drawable_preview.png")
            else:
                shutil.copy2(self.build_dir / "res" / "raw" / "watchface.xml",
                             self.compiled_dir / "res_raw_watchface.xml")
                shutil.copy2(self.build_dir / "res" / "drawable" / "preview.png",
                             self.compiled_dir / "res_drawable_preview.png")
            self.log("  aapt2 unavailable: using verified precompiled ARM template")
            return

        compiled_res = self.build_dir / "compiled_res.zip"
        cmd = [str(AAPT2), "compile", "--dir", str(self.build_dir / "res"), "-o", str(compiled_res)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"aapt2 compile failed:\n{r.stderr}")
        self.log("  aapt2 compile: OK")

        template_apk = self.build_dir / "template.apk"
        cmd = [
            str(AAPT2), "link",
            "-o", str(template_apk),
            "--manifest", str(self.build_dir / "AndroidManifest.xml"),
            "-I", str(ANDROID_JAR),
            "--no-static-lib-packages",
            str(compiled_res),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"aapt2 link failed:\n{r.stderr}")
        self.log(f"  aapt2 link: OK ({template_apk.stat().st_size} bytes)")

        # Extract all compiled resources from template APK
        self.compiled_dir.mkdir(parents=True, exist_ok=True)

        # Determine which files to extract (scan template APK)
        extract_files = []
        with zipfile.ZipFile(template_apk, "r") as zf:
            for name in zf.namelist():
                if name.startswith("META-INF/"):
                    continue
                extract_files.append(name)

        with zipfile.ZipFile(template_apk, "r") as zf:
            for name in extract_files:
                data = zf.read(name)
                out_name = name.replace("/", "_")
                (self.compiled_dir / out_name).write_bytes(data)
                self.log(f"  Extracted: {name} ({len(data)}B)")

    def build_final_apk(self) -> Path:
        if not APKSIGNER.is_file():
            raise RuntimeError(
                f"apksigner not found at {APKSIGNER}; set ANDROID_HOME or APKSIGNER"
            )
        if not KEYSTORE.is_file():
            raise RuntimeError(f"keystore not found at {KEYSTORE}")
        # Resolve signing config (dev default vs production fail-closed, S1)
        sign_cfg = resolve_signing_config()
        # Determine which compiled files go into the final APK
        # Rules:
        #   - AndroidManifest.xml → always (binary AXML, DEFLATE)
        #   - resources.arsc → always (STORED + 4-byte aligned)
        #   - res/raw/* → always (raw text XML or other, DEFLATE)
        #   - res/xml/* → always (binary AXML, DEFLATE)
        #   - res/drawable/* → if exists (DEFLATE)
        #   - res/font/* → if exists (DEFLATE)
        #   - res/values/* → NEVER (already compiled into resources.arsc)

        SKIP_PATTERNS = ["res/values/"]  # values are compiled into resources.arsc

        entries = []
        for f in sorted(self.compiled_dir.iterdir()):
            arc_name = f.name.replace("_", "/", 1)  # e.g. res_raw_watchface.xml -> res/raw/watchface.xml
            # But we stored as: AndroidManifest.xml, resources.arsc, res_raw_watchface.xml, etc.
            # Need to reconstruct proper archive path
            if f.name == "AndroidManifest.xml":
                arc_name = "AndroidManifest.xml"
                method = "deflate"
            elif f.name == "resources.arsc":
                arc_name = "resources.arsc"
                method = "store"  # MUST be uncompressed+aligned
            else:
                # Reconstruct path: res_raw_watchface.xml → res/raw/watchface.xml
                parts = f.name.split("_", 2)
                if len(parts) >= 3:
                    arc_name = parts[0] + "/" + parts[1] + "/" + parts[2]
                elif len(parts) == 2:
                    arc_name = parts[0] + "/" + parts[1]
                else:
                    arc_name = f.name

                # Skip res/values/ (already in resources.arsc)
                if any(arc_name.startswith(p) for p in SKIP_PATTERNS):
                    continue

                method = "deflate"

            entries.append((f, arc_name, method))

        self.log(f"  Entries to pack: {len(entries)}")
        for _, name, method in entries:
            self.log(f"    {name:50s} {method}")

        unsigned_apk = self.build_dir / "unsigned.apk"
        self._write_aligned_zip(unsigned_apk, entries)
        self.log(f"  APK packaged (aligned): {unsigned_apk.stat().st_size} bytes")

        # Verify alignment
        self._verify_alignment(unsigned_apk)

        # Sign
        signed_apk = self.project_dir / f"{self.config['package_name'].split('.')[-1]}-watchface.apk"
        cmd = [
            str(APKSIGNER), "sign",
            "--ks", str(sign_cfg.keystore),
            "--ks-key-alias", sign_cfg.alias,
            "--ks-pass", sign_cfg.ks_pass_ref,   # env:/file:/pass: 引用形式
            "--key-pass", sign_cfg.key_pass_ref,
            "--out", str(signed_apk),
            str(unsigned_apk),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("apksigner failed:\n" + _scrub_apksigner_error(r.stderr))
        self.log(f"  Signed: {signed_apk.name} ({signed_apk.stat().st_size} bytes)")

        # Verify signature
        cmd = [str(APKSIGNER), "verify", "--verbose", str(signed_apk)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"Signature verification failed:\n{r.stderr}")
        self.log("  Verified: PASS (v1+v2+v3)")

        # Final contents
        self.log("\n  Final APK contents:")
        with zipfile.ZipFile(signed_apk, "r") as zf:
            for info in zf.infolist():
                method = "STORED" if info.compress_type == 0 else "DEFLATE"
                data_offset = info.header_offset + 30 + len(info.filename) + len(info.extra)
                aligned = "OK" if data_offset % 4 == 0 else "MISALIGNED"
                self.log(f"    {info.filename:50s} {info.file_size:>8d}B  {method:8s}  @{data_offset} ({aligned})")

        return signed_apk

    def _write_aligned_zip(self, path: Path, entries: list):
        """Write a ZIP with all entries aligned to 4-byte boundaries.

        Uses ZIP extra field (header_id=0xD935) to pad each entry
        so data offset is 4-byte aligned. Same technique as Android's zipalign.
        """
        ALIGN = ALIGNMENT
        EXTRA_SIZES = {0: 0, 1: 7, 2: 6, 3: 5}

        buf = bytearray()
        cd_entries = []
        offset = 0

        for src_path, arc_name, method in entries:
            data = src_path.read_bytes()
            filename_bytes = arc_name.encode("utf-8")

            if method == "deflate":
                compressor = zlib.compressobj(6, zlib.DEFLATED, -15)
                compressed = compressor.compress(data) + compressor.flush()
                compress_type = 8
            else:
                compressed = data
                compress_type = 0

            crc = binascii.crc32(data) & 0xFFFFFFFF

            base = offset + 30 + len(filename_bytes)
            remainder = base % ALIGN
            extra_size = EXTRA_SIZES[remainder]

            if extra_size == 0:
                extra = b""
            else:
                padding_len = extra_size - 4
                extra = struct.pack("<HH", 0xD935, padding_len) + b"\x00" * padding_len

            data_offset = offset + 30 + len(filename_bytes) + len(extra)
            assert data_offset % ALIGN == 0, f"{arc_name}: @{data_offset} not aligned"

            local_header = struct.pack(
                "<4sHHHHHIIIHH",
                b"PK\x03\x04",
                20, 0,
                compress_type,
                0, 0,
                crc,
                len(compressed),
                len(data),
                len(filename_bytes),
                len(extra),
            )

            buf.extend(local_header)
            buf.extend(filename_bytes)
            buf.extend(extra)
            buf.extend(compressed)

            cd_entries.append({
                "filename": arc_name,
                "offset": offset,
                "crc": crc,
                "compressed_size": len(compressed),
                "uncompressed_size": len(data),
                "compress_type": compress_type,
                "extra": extra,
            })
            offset += len(local_header) + len(filename_bytes) + len(extra) + len(compressed)

        cd_offset = offset
        for entry in cd_entries:
            filename_bytes = entry["filename"].encode("utf-8")
            extra = entry["extra"]
            cd_entry = struct.pack(
                "<4sHHHHHHIIIHHHHHII",
                b"PK\x01\x02",
                20, 20,
                0,
                entry["compress_type"],
                0, 0,
                entry["crc"],
                entry["compressed_size"],
                entry["uncompressed_size"],
                len(filename_bytes),
                len(extra),
                0, 0, 0, 0,
                entry["offset"],
            )
            buf.extend(cd_entry)
            buf.extend(filename_bytes)
            buf.extend(extra)
            offset += len(cd_entry) + len(filename_bytes) + len(extra)

        cd_size = offset - cd_offset
        eocd = struct.pack(
            "<4sHHHHIIH",
            b"PK\x05\x06",
            0, 0,
            len(cd_entries),
            len(cd_entries),
            cd_size,
            cd_offset,
            0,
        )
        buf.extend(eocd)

        with open(path, "wb") as f:
            f.write(buf)

    def _verify_alignment(self, apk_path: Path):
        with zipfile.ZipFile(apk_path, "r") as zf:
            for info in zf.infolist():
                data_offset = info.header_offset + 30 + len(info.filename) + len(info.extra)
                method = "STORED" if info.compress_type == 0 else "DEFLATE"
                status = "OK" if data_offset % ALIGNMENT == 0 else "MISALIGNED"
                self.log(f"    {info.filename:50s} {method:8s} @{data_offset} ({status})")

    def build(self) -> Path:
        self.log("=" * 60)
        self.log(f"WFF Builder — {self.project_dir.name}")
        self.log("=" * 60)

        self.log("\n[1/5] Load config")
        self.load_config()
        self.log(f"  Package: {self.config['package_name']}")
        self.log(f"  Version: {self.config['version_code']} ({self.config['version_name']})")

        self.log("\n[2/5] Validate watchface.xml")
        wf_text = (self.project_dir / "watchface.xml").read_text()
        failures = validate_watchface_xml(wf_text, verbose=self.verbose)
        errors = [f for f in failures if f["severity"] == "error"]
        warnings = [f for f in failures if f["severity"] == "warn"]
        if errors:
            self.log(f"\n  {len(errors)} ERROR(S) — must fix before build:")
            for f in errors:
                self.log(f"    [{f['rule_id']}] {f['detail']}")
                self.log(f"      Fix: {f['fix']}")
                if f["examples"].get("bad"):
                    self.log(f"      Bad:  {f['examples']['bad']}")
                if f["examples"].get("good"):
                    self.log(f"      Good: {f['examples']['good']}")
            raise ValueError(f"{len(errors)} validation error(s) — fix and rebuild")
        if warnings:
            self.log(f"\n  {len(warnings)} warning(s):")
            for f in warnings:
                self.log(f"    [{f['rule_id']}] {f['detail']}")
                self.log(f"      Fix: {f['fix']}")
        else:
            self.log("  All rules passed")

        self.log("\n[3/5] Generate resources")
        self.build_dir.mkdir(parents=True, exist_ok=True)
        self.generate_manifest()
        self.generate_resource_files()

        self.log("\n[4/5] Compile (aapt2)")
        self.compile_resources()

        self.log("\n[5/5] Package + Sign")
        signed_apk = self.build_final_apk()

        self.log(f"\n{'=' * 60}")
        self.log(f"Done: {signed_apk}")
        self.log(f"Size: {signed_apk.stat().st_size:,} bytes")
        self.log(f"{'=' * 60}")
        return signed_apk

    @staticmethod
    def init_project(project_dir: str):
        pdir = Path(project_dir)
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "project.yaml").write_text(PROJECT_YAML_TEMPLATE)
        (pdir / "watchface.xml").write_text(
            '<?xml version="1.0"?>\n'
            '<WatchFace width="450" height="450">\n'
            '    <Metadata key="CLOCK_TYPE" value="DIGITAL"/>\n'
            '    <Metadata key="PREVIEW_TIME" value="10:08:32"/>\n'
            '    <Scene backgroundColor="#ff000000">\n'
            '        <DigitalClock x="0" y="0" width="450" height="450">\n'
            '            <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE"\n'
            '                      align="CENTER" x="0" y="150" width="450" height="120" alpha="255">\n'
            '                <Variant mode="AMBIENT" target="alpha" value="0"/>\n'
            '                <Font family="SYNC_TO_DEVICE" size="100" weight="BOLD" color="#ff00F5FF"/>\n'
            '            </TimeText>\n'
            '            <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE"\n'
            '                      align="CENTER" x="0" y="150" width="450" height="120" alpha="0">\n'
            '                <Variant mode="AMBIENT" target="alpha" value="255"/>\n'
            '                <Font family="SYNC_TO_DEVICE" size="100" weight="THIN" color="#ff888888"/>\n'
            '            </TimeText>\n'
            '        </DigitalClock>\n'
            '    </Scene>\n'
            '</WatchFace>\n'
        )
        print(f"Initialized project in {pdir}/")
        print("  project.yaml   — edit package name, version, etc.")
        print("  watchface.xml  — edit your watch face design")
        print("  preview.png    — add a preview image (same size as canvas, e.g. 450x450)")
        print(f"\nBuild with: python wff_builder.py build {pdir}")


# ─── CLI ──────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python wff_builder.py init     <project_dir>  — create new project")
        print("  python wff_builder.py validate <project_dir>  — check watchface.xml rules")
        print("  python wff_builder.py build    <project_dir>  — build APK")
        sys.exit(1)

    cmd = sys.argv[1]
    project_dir = sys.argv[2]

    if cmd == "init":
        WFFBuilder.init_project(project_dir)
    elif cmd == "validate":
        wf_path = Path(project_dir) / "watchface.xml"
        if not wf_path.exists():
            print(f"Error: {wf_path} not found")
            sys.exit(1)
        wf_text = wf_path.read_text()
        print(f"Validating {wf_path.name}...")
        failures = validate_watchface_xml(wf_text, verbose=True)
        # R33 项目级检查 (watch_face_info.xml 独立于 watchface.xml)
        # 分级: 文件不存在 → warn (builder build 自动生成含 Editable 的模板);
        #       文件存在但缺 Editable → error (明确 bug: 开关没开, 编辑器无自定义入口)
        info_ok, info_detail = check_watch_face_info(project_dir)
        info_missing = info_detail.startswith("res/xml/watch_face_info.xml 不存在")
        if not info_ok:
            sev = "warn" if info_missing else "error"
            failures.append({"rule_id": "R33", "severity": sev,
                         "detail": info_detail,
                         "fix": "res/xml/watch_face_info.xml 加 <Editable value=\"true\"/>",
                         "examples": {"good": "<WatchFaceInfo><Preview value=\"@drawable/preview\"/><Editable value=\"true\"/></WatchFaceInfo>"}}
            )
            print(f"  [{'FAIL' if sev == 'error' else 'WARN'}] R33: {info_detail}")
        else:
            print(f"  [PASS] R33: OK (watch_face_info.xml 含 Editable)")
        errors = [f for f in failures if f["severity"] == "error"]
        warnings = [f for f in failures if f["severity"] == "warn"]
        total = len(WFF_RULES) + 1  # + R33 项目级
        print(f"\nSummary: {total - len(failures)}/{total} passed, {len(errors)} errors, {len(warnings)} warnings")
        if errors:
            sys.exit(1)
    elif cmd == "build":
        builder = WFFBuilder(project_dir)
        apk = builder.build()
        print(f"\nAPK: {apk}")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
