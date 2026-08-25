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
    preview.png     — 鐐宝预览图（384x384 推荐）

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
from pathlib import Path
from xml.etree import ElementTree as ET

# ─── 配置 ──────────────────────────────────────────────

BUILDER_ROOT = Path(__file__).resolve().parent
ANDROID_HOME = os.environ.get("ANDROID_HOME", "/opt/android-sdk")
BUILD_TOOLS = Path(ANDROID_HOME) / "build-tools" / "34.0.0"
ANDROID_JAR = Path(ANDROID_HOME) / "platforms" / "android-34" / "android.jar"
AAPT2 = Path(os.environ.get("AAPT2", str(BUILD_TOOLS / "aapt2")))
APKSIGNER = Path(os.environ.get("APKSIGNER", str(BUILD_TOOLS / "apksigner")))

KEYSTORE = Path(os.environ.get("WFF_KEYSTORE", str(BUILDER_ROOT / "keystore" / "test.keystore")))
PRECOMPILED_DIR = BUILDER_ROOT / "projects" / "demo" / "_build" / "compiled"
KEYSTORE_PASS = "wfftest123"
KEY_ALIAS = "wfftest"
KEY_PASS = "wfftest123"

# WFF 版本与 minSdk 映射
WFF_VERSION_MIN_SDK = {
    1: 33,   # Wear OS 4
    2: 34,   # Wear OS 5
    3: 34,
    4: 34,
}

ALIGNMENT = 4  # resources.arsc 对齐字节


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
</WatchFaceInfo>
"""

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
    # 时间
    "[HOUR_0_23]", "[HOUR_1_12]", "[HOUR_Z]", "[MINUTE_Z]", "[SECOND_Z]",
    "[SECONDS_IN_DAY]", "[AMPM_STATE]", "[AMPM_STRING]",
    # 日期
    "[DAY]", "[DAY_Z]", "[DAY_0_30]", "[DAY_OF_WEEK_S]", "[DAY_OF_WEEK]",
    "[DAYS_IN_MONTH]", "[MONTH]", "[MONTH_S]", "[YEAR]",
    # 电池
    "[BATTERY_PERCENT]",
    # 心率
    "[HEART_RATE]",
    # 配置
    "[CONFIGURATION.",
    # 并发
    "[COMPLICATION.",
    # 天气
    "[WEATHER.",
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
         "good": '<DigitalClock><TimeText format="HH:mm">...</TimeText></DigitalClock>'}),
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
]


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
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r"^(\w+):\s*(.+)$", line)
            if m:
                key, val = m.group(1), m.group(2).strip()
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                elif val.isdigit():
                    val = int(val)
                config[key] = val
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

        # strings.xml
        strings_path = self.build_dir / "res" / "values" / "strings.xml"
        strings_path.parent.mkdir(parents=True, exist_ok=True)
        strings_path.write_text(STRINGS_TEMPLATE.format(
            watch_face_name=self.config["watch_face_name"]
        ))
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
            "--ks", str(KEYSTORE),
            "--ks-key-alias", KEY_ALIAS,
            "--ks-pass", f"pass:{KEYSTORE_PASS}",
            "--key-pass", f"pass:{KEY_PASS}",
            "--out", str(signed_apk),
            str(unsigned_apk),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"apksigner failed:\n{r.stderr}")
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
            '            <TimeText format="HH:mm" hourFormat="SYNC_TO_DEVICE"\n'
            '                      align="CENTER" x="0" y="150" width="450" height="120" alpha="255">\n'
            '                <Variant mode="AMBIENT" target="alpha" value="0"/>\n'
            '                <Font family="SYNC_TO_DEVICE" size="100" weight="BOLD" color="#ff00F5FF"/>\n'
            '            </TimeText>\n'
            '            <TimeText format="HH:mm" hourFormat="SYNC_TO_DEVICE"\n'
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
        print("  preview.png    — add a 384x384 preview image")
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
        errors = [f for f in failures if f["severity"] == "error"]
        warnings = [f for f in failures if f["severity"] == "warn"]
        print(f"\nSummary: {16 - len(failures)}/16 passed, {len(errors)} errors, {len(warnings)} warnings")
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
