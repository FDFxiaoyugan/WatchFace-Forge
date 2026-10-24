#!/usr/bin/env python3
"""unpack-audit: 第三方表盘 APK 解包审计 + 语料回填 + 矛盾扫描 (REPAIR_PLAN P4)

用法:
    python tools/unpack_audit.py scan <apk-or-source-dir>       # 单样本审计报告
    python tools/unpack_audit.py corpus <path> --name NAME --license L --source URL
                                                                 # 审计 + 写入语料库
    python tools/unpack_audit.py scan-contradictions             # 语料库 × 负面断言交叉扫描

输入形态:
    - .apk 文件 → unzip → res/raw/watchface.xml (明文) + 二进制 AndroidManifest 解析
    - 源码目录   → 递归找 watchface.xml + 文本 AndroidManifest.xml 解析

矛盾扫描 (scan-contradictions):
    tools/contradiction_claims.json 登记规则层负面断言 (元素 × 声称不渲染的版本集);
    语料中任何上架/可用成品在声称不支持的版本上使用了该元素 → 红牌。
    堵死 2026-09-22 型失败 (反证躺在调研文档里一个月无人对照)。

证据等级约定: 语料条目 = 成品实证 (第三方向量); 红牌 = 必须重验的断言。
"""
import argparse
import json
import re
import struct
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

REPO = Path(__file__).resolve().parent.parent
CORPUS_DIR = REPO / "skills" / "wff-watchface-dev" / "data" / "corpus"
CLAIMS_PATH = REPO / "tools" / "contradiction_claims.json"

WFF_VERSION_PROP = "com.google.wear.watchface.format.version"

# ---------- 二进制 AXML Manifest 解析 (Rush-Hour 实证过的解析器) ----------

def parse_axml(raw: bytes) -> dict:
    pos, strings, sp_end = 8, [], 0
    out = {"package": None, "minSdk": None, "targetSdk": None, "wff_version": None}
    while pos < len(raw) - 8:
        ctype, _, csize = struct.unpack_from("<HHI", raw, pos)
        if ctype == 0x0001:
            count, _styles, flags, sstart, _ = struct.unpack_from("<IIIII", raw, pos + 8)
            utf8 = bool(flags & 0x100)
            base = pos + sstart
            for i in range(count):
                off = struct.unpack_from("<I", raw, pos + 28 + 4 * i)[0]
                p = base + off
                if utf8:
                    l1 = raw[p]; p += 1
                    if l1 & 0x80: p += 1
                    s = raw[p:p + l1].decode("utf-8", "ignore")
                else:
                    l1 = struct.unpack_from("<H", raw, p)[0]; p += 2
                    s = raw[p:p + l1 * 2].decode("utf-16-le", "ignore")
                strings.append(s)
            sp_end = pos + csize
        if csize == 0:
            break
        pos += csize
    S = lambda i: strings[i] if isinstance(i, int) and 0 <= i < len(strings) else None
    pos = sp_end
    while pos < len(raw) - 8:
        ctype, _, csize = struct.unpack_from("<HHI", raw, pos)
        if ctype == 0x0102:
            name_idx = struct.unpack_from("<I", raw, pos + 20)[0]
            attr_count = struct.unpack_from("<H", raw, pos + 28)[0]
            en = S(name_idx)
            attrs = []
            for i in range(attr_count):
                a = pos + 36 + i * 20
                n_, rawv = struct.unpack_from("<II", raw, a + 4)
                dt = raw[a + 15]
                data = struct.unpack_from("<I", raw, a + 16)[0]
                attrs.append((S(n_), S(rawv) if dt == 0x03 else data))
            if en == "manifest":
                for n, v in attrs:
                    if n == "package":
                        out["package"] = v
            if en == "uses-sdk":
                for n, v in attrs:
                    if n == "minSdkVersion":
                        out["minSdk"] = v
                    if n == "targetSdkVersion":
                        out["targetSdk"] = v
            if en == "property":
                if any(v == WFF_VERSION_PROP for _, v in attrs):
                    for n, v in attrs:
                        if n == "value":
                            out["wff_version"] = v
        pos += csize
    return out

# ---------- 文本 Manifest 解析 (源码目录形态) ----------

def parse_text_manifest(path: Path) -> dict:
    out = {"package": None, "minSdk": None, "targetSdk": None, "wff_version": None}
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return out
    root = tree.getroot()
    out["package"] = root.get("package")
    ns = "{http://schemas.android.com/apk/res/android}"
    uses = root.find("uses-sdk")
    if uses is not None:
        out["minSdk"] = uses.get(ns + "minSdkVersion")
        out["targetSdk"] = uses.get(ns + "targetSdkVersion")
    for prop in root.iter("property"):
        if prop.get(ns + "name") == WFF_VERSION_PROP:
            out["wff_version"] = prop.get(ns + "value")
    return out

# ---------- 解包与清单 ----------

def inventory(xml_text: str) -> dict:
    counts = {}
    for m in re.finditer(r"<([A-Z][A-Za-z0-9]+)", xml_text):
        counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    sources = sorted(set(re.findall(r"\[([A-Z_0-9]+)\]", xml_text)))
    resources = sorted(set(re.findall(r'resource="([^"]+)"', xml_text)))
    return {"construct_counts": counts, "data_sources": sources,
            "resource_refs": resources, "xml_bytes": len(xml_text.encode("utf-8"))}

def extract(path: Path) -> dict:
    """返回审计 dict; kind ∈ {wff-apk, wff-source, code-based, unknown}"""
    entry = {"input": str(path), "extracted_at": datetime.now(timezone.utc).isoformat()}
    if path.is_file() and path.suffix == ".apk":
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(path) as z:
                names = z.namelist()
                has_code = any(n == "classes.dex" for n in names)
                wf = [n for n in names if n == "res/raw/watchface.xml"]
                mf = [n for n in names if n == "AndroidManifest.xml"]
                if not wf and has_code:
                    entry["kind"] = "code-based"
                    entry["note"] = "含 classes.dex → WFS/Canvas 代码栈 (非 WFF)"
                    return entry
                if not wf:
                    entry["kind"] = "unknown"
                    entry["note"] = "APK 内无 res/raw/watchface.xml 且无 dex"
                    return entry
                xml_text = z.read(wf[0]).decode("utf-8", "ignore")
                entry.update(inventory(xml_text))
                entry["kind"] = "wff-apk"
                if mf:
                    entry.update(parse_axml(z.read(mf[0])))
        entry["apk_bytes"] = path.stat().st_size
        return entry
    if path.is_dir():
        wf_files = sorted(path.rglob("watchface.xml"))
        mf_files = [p for p in path.rglob("AndroidManifest.xml")
                    if "build" not in p.parts and "_build" not in p.parts]
        if not wf_files:
            entry["kind"] = "unknown"
            entry["note"] = "未找到 watchface.xml (可能未包含 res/raw 或非 WFF)"
            return entry
        xml_text = wf_files[0].read_text(encoding="utf-8", errors="ignore")
        entry.update(inventory(xml_text))
        entry["kind"] = "wff-source"
        entry["watchface_xml_path"] = str(wf_files[0])
        if mf_files:
            entry.update(parse_text_manifest(mf_files[0]))
        return entry
    entry["kind"] = "unknown"
    return entry

# ---------- 语料库与矛盾扫描 ----------

def corpus_write(path: Path, name: str, license_note: str, source_url: str):
    entry = extract(path)
    entry.update({"name": name, "license": license_note, "source": source_url})
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    out = CORPUS_DIR / f"{name}.json"
    out.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry, out

def load_claims() -> list:
    if not CLAIMS_PATH.exists():
        return []
    return json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))

def scan_contradictions() -> int:
    claims = load_claims()
    entries = sorted(CORPUS_DIR.glob("*.json")) if CORPUS_DIR.exists() else []
    print(f"语料 {len(entries)} 条 × 负面断言 {len(claims)} 条\n")
    red = 0
    for e_path in entries:
        e = json.loads(e_path.read_text(encoding="utf-8"))
        if e.get("kind") not in ("wff-apk", "wff-source"):
            continue
        fv = e.get("wff_version")
        if isinstance(fv, str) and fv.isdigit():
            fv = int(fv)
        counts = e.get("construct_counts", {})
        for c in claims:
            hit = [el for el in c["elements"] if el in counts]
            if not hit:
                continue
            broken = c.get("broken_versions", ["all"])
            in_scope = "all" in broken or fv in broken
            if in_scope:
                red += 1
                print(f"[红牌] {e['name']} (format.version={fv}) 使用 {hit} × "
                      f"{c['id']} 声称「{c['claim']}」(声称失效版本: {broken}) "
                      f"— 断言与上架成品矛盾, 必须重验")
    if red == 0:
        print("无红牌: 当前负面断言与语料一致")
    else:
        print(f"\n共 {red} 处矛盾 → 修订规则层 (成品实证 > 我方未过)")
    return 1 if red else 0

# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s1 = sub.add_parser("scan"); s1.add_argument("path")
    s2 = sub.add_parser("corpus"); s2.add_argument("path")
    s2.add_argument("--name", required=True)
    s2.add_argument("--license", default="未标注")
    s2.add_argument("--source", default="")
    sub.add_parser("scan-contradictions")
    a = ap.parse_args()
    if a.cmd == "scan":
        r = extract(Path(a.path))
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif a.cmd == "corpus":
        entry, out = corpus_write(Path(a.path), a.name, a.license, a.source)
        print(f"已写入 {out}")
        print(f"  kind={entry.get('kind')} format.version={entry.get('wff_version')} "
              f"元素种类={len(entry.get('construct_counts', {}))}")
    else:
        sys.exit(scan_contradictions())

if __name__ == "__main__":
    main()
