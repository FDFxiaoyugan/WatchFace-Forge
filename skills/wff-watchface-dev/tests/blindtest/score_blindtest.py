#!/usr/bin/env python3
"""Blind Test Scorer — 盲测交付物自动评分（Phase 4C / P4B-F06）

对盲测 agent 产出的表盘项目执行三层评分：
  1. static  — 需求卡验收标准的静态 XML 检查（criteria.json）
  2. validate — wff-builder 16 条规则
  3. build   — APK 产出 + 签名 + sha256

用法:
  # 单卡评分
  python3 score_blindtest.py BT-01 /path/to/project [--rounds N] [--json out.json]

  # 全卡汇总（目录约定: runs_dir/BT-01/ ... BT-05/ 各为项目目录）
  # 可选 runs_dir/runs.json 记录每卡修复轮数: {"BT-01": {"rounds": 2}, ...}
  python3 score_blindtest.py --all runs_dir [--json out.json] [--markdown report.md]

评分不含视觉项（布局溢出/重叠/ambient 可读性）——按 v3.0 由人工或 VLM 抽查。

Exit code: 0 = 全部通过, 1 = 有失败项, 2 = 用法错误
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CRITERIA = json.loads((HERE / "criteria.json").read_text(encoding="utf-8"))
REPO_ROOT = HERE.parents[3]          # watchface-forge/
WFF_BUILDER = REPO_ROOT / "wff-builder" / "wff_builder.py"

CARD_IDS = ["BT-01", "BT-02", "BT-03", "BT-04", "BT-05"]


# ---------- helpers ----------

# WFF SDK 默认探测路径（TOOLS.md 约定），scorer 子进程自动注入 ANDROID_HOME
SDK_CANDIDATES = [
    Path("/home/z/my-project/tools/android-sdk"),
    Path("/opt/android-sdk"),
]


def build_env():
    """Env for subprocesses: ensure ANDROID_HOME points to an existing SDK."""
    env = dict(os.environ)
    if not env.get("ANDROID_HOME"):
        for cand in SDK_CANDIDATES:
            if (cand / "build-tools" / "34.0.0" / "apksigner").exists():
                env["ANDROID_HOME"] = str(cand)
                break
    return env


def run_cmd(cmd, timeout=180):
    """Run subprocess, return (rc, stdout+stderr)."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           env=build_env())
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"
    except FileNotFoundError as e:
        return 127, str(e)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------- scoring layers ----------

def score_static(card_id, project_dir):
    """Layer 1: static XML checks per criteria.json."""
    xml_path = project_dir / "watchface.xml"
    if not xml_path.exists():
        return {"error": "watchface.xml not found",
                "checks": [], "score": 0, "max": 1}

    xml = xml_path.read_text(encoding="utf-8", errors="replace")
    spec = CRITERIA.get(card_id, {})
    checks, score, max_score = [], 0, 0

    for c in spec.get("static_checks", []):
        # 先剥 XML 注释: 注释里的示例文字不应参与评分 (与 wff_builder 同口径, 防误报)
        scanned = re.sub(r"<!--.*?-->", "", xml, flags=re.S)
        matches = re.findall(c["pattern"], scanned, re.DOTALL)
        min_count = c.get("min_count", 1)
        if c.get("negative"):
            # 负向检查: pattern 必须零命中才 PASS (幽灵写法/非法属性探测)
            passed = len(matches) == 0
        else:
            passed = len(matches) >= min_count
        weight = c["weight"]
        max_score += weight
        if passed:
            score += weight
        checks.append({
            "id": c["id"], "desc": c["desc"], "passed": passed,
            "matched": len(matches),
            "required": 0 if c.get("negative") else min_count,
            "weight": weight,
        })

    return {"checks": checks, "score": score, "max": max_score, "error": None}


def score_validate(project_dir):
    """Layer 2: wff-builder validate (24 rules, v0.4.0).

    口径: error 才挂 (rc != 0 或 errors > 0); warning 不算失败——
    warn 语义是提示 (R33 无文件提示 / R34 圆屏溢出提示), builder build 同样不因 warn 阻断。
    """
    rc, out = run_cmd([sys.executable, str(WFF_BUILDER), "validate", str(project_dir)])
    m = re.search(r"Summary:\s*(\d+)/(\d+) passed,\s*(\d+) errors?,\s*(\d+) warnings?", out)
    if not m:
        return {"passed": False, "rule_summary": None, "raw_tail": out.strip().splitlines()[-3:] if out.strip() else "no output", "rc": rc}
    passed, total, errors, warnings = int(m[1]), int(m[2]), int(m[3]), int(m[4])
    return {
        "passed": rc == 0 and errors == 0,
        "rule_summary": f"{passed}/{total} passed, {errors} errors, {warnings} warnings",
        "rc": rc,
    }


def score_build(project_dir):
    """Layer 3: wff-builder build → APK exists + sha256."""
    rc, out = run_cmd([sys.executable, str(WFF_BUILDER), "build", str(project_dir)], timeout=300)
    apk_m = re.search(r"APK:\s*(.+\.apk)", out)
    if rc != 0 or not apk_m:
        return {"passed": False, "apk": None, "rc": rc,
                "raw_tail": out.strip().splitlines()[-3:] if out.strip() else "no output"}
    apk_path = Path(apk_m.group(1).strip())
    if not apk_path.exists() or apk_path.stat().st_size == 0:
        return {"passed": False, "apk": str(apk_path), "error": "APK missing or empty", "rc": rc}
    signed = "PASS" in out and ("v1+v2" in out or "signature" in out.lower() or "签名" in out)
    return {"passed": True, "apk": str(apk_path), "size_bytes": apk_path.stat().st_size,
            "sha256": sha256_of(apk_path), "signed": signed, "rc": rc}


def score_card(card_id, project_dir, rounds=None):
    """Full scoring for one card. Returns result dict."""
    project_dir = Path(project_dir).resolve()
    result = {
        "card_id": card_id,
        "title": CRITERIA.get(card_id, {}).get("title", "?"),
        "project_dir": str(project_dir),
        "rounds": rounds,
    }

    if not project_dir.is_dir():
        result.update({"status": "error", "error": f"project dir not found: {project_dir}"})
        return result

    static = score_static(card_id, project_dir)
    validate = score_validate(project_dir)
    build = score_build(project_dir)

    result.update({
        "static": static,
        "validate": validate,
        "build": build,
    })

    assumptions = project_dir / "ASSUMPTIONS.md"
    result["assumptions_md"] = assumptions.exists()

    all_pass = (static.get("error") is None and static["score"] == static["max"]
                and validate["passed"] and build["passed"])
    result["status"] = "pass" if all_pass else "fail"
    return result


# ---------- reports ----------

def fmt_card_report(r):
    """Human-readable per-card report."""
    lines = []
    lines.append(f"## {r['card_id']} — {r['title']}  [{'PASS' if r['status']=='pass' else 'FAIL'}]")
    lines.append(f"- 项目: `{r['project_dir']}`")
    if r.get("error"):
        lines.append(f"- ❌ 错误: {r['error']}")
        return "\n".join(lines)
    if r.get("rounds"):
        lines.append(f"- 修复轮数: {r['rounds']}")
    lines.append(f"- ASSUMPTIONS.md: {'✅' if r.get('assumptions_md') else '❌ 缺失'}")

    s = r.get("static")
    if s:
        if s.get("error"):
            lines.append(f"- 静态检查: ❌ {s['error']}")
        else:
            lines.append(f"- 静态检查: {s['score']}/{s['max']}")
            for c in s["checks"]:
                mark = "✅" if c["passed"] else "❌"
                extra = f" (匹配{c['matched']}/需{c['required']})" if not c["passed"] else ""
                lines.append(f"  - {mark} {c['id']}: {c['desc']}{extra}")

    v = r.get("validate")
    if v:
        if v.get("rule_summary"):
            lines.append(f"- validate: {'✅' if v['passed'] else '❌'} {v['rule_summary']}")
        else:
            lines.append(f"- validate: ❌ {v.get('raw_tail')}")

    b = r.get("build")
    if b:
        if b["passed"]:
            kb = b["size_bytes"] / 1024
            lines.append(f"- build: ✅ APK {kb:.1f}KB 签名={'✅' if b['signed'] else '?'}")
            lines.append(f"  - sha256: `{b['sha256'][:16]}…`")
        else:
            lines.append(f"- build: ❌ {b.get('error') or b.get('raw_tail')}")
    return "\n".join(lines)


def summarize(results):
    """v3.0 Phase 4 总验收指标映射."""
    n = len(results)
    validated = [r for r in results if r.get("validate", {}).get("passed")]
    built = [r for r in results if r.get("build", {}).get("passed")]
    static_full = [r for r in results if r.get("static", {}).get("score") == r.get("static", {}).get("max")]

    with_rounds = [r for r in results if r.get("rounds")]
    first_pass = [r for r in with_rounds if r["rounds"] == 1 and r.get("validate", {}).get("passed")]
    avg_rounds = (sum(r["rounds"] for r in with_rounds) / len(with_rounds)) if with_rounds else None

    return {
        "cards_total": n,
        "static_full_pass": f"{len(static_full)}/{n}",
        "validate_pass": f"{len(validated)}/{n}",
        "build_pass": f"{len(built)}/{n}",
        "build_rate_of_validated": f"{len(built)}/{len(validated)}" if validated else "n/a",
        "first_pass_rate": f"{len(first_pass)}/{len(with_rounds)}" if with_rounds else "n/a (需 rounds 数据)",
        "avg_fix_rounds": (round(avg_rounds, 2) if avg_rounds is not None else None),
        "v3_0_targets": {
            "validate_first_pass": ">=60% (>=3/5)",
            "fix_rounds_avg": "<=3",
            "build_success": "100% of validated",
            "real_device": "人工抽查 >=2 张（本脚本不评）",
        },
    }


def main():
    ap = argparse.ArgumentParser(description="Blind test scorer")
    ap.add_argument("card_id", nargs="?", help="BT-01..BT-05")
    ap.add_argument("project_dir", nargs="?", help="path to project dir")
    ap.add_argument("--all", metavar="RUNS_DIR", help="score all cards under runs_dir/BT-0X/")
    ap.add_argument("--rounds", type=int, default=None, help="fix rounds (conductor-recorded)")
    ap.add_argument("--json", metavar="OUT", help="write JSON report to file")
    ap.add_argument("--markdown", metavar="OUT", help="write markdown report to file (--all only)")
    args = ap.parse_args()

    if args.all:
        runs_dir = Path(args.all).resolve()
        if not runs_dir.is_dir():
            print(f"Error: {runs_dir} not found", file=sys.stderr)
            sys.exit(2)
        rounds_map = {}
        rounds_file = runs_dir / "runs.json"
        if rounds_file.exists():
            try:
                rounds_map = json.loads(rounds_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                print(f"WARN: invalid runs.json, ignoring", file=sys.stderr)

        results, missing = [], []
        for cid in CARD_IDS:
            pdir = runs_dir / cid
            if pdir.is_dir():
                results.append(score_card(cid, pdir, rounds=rounds_map.get(cid, {}).get("rounds")))
            else:
                missing.append(cid)

        summary = summarize(results)
        md = ["# 盲测评分报告", "",
              f"运行目录: `{runs_dir}`",
              f"缺失卡片: {', '.join(missing) if missing else '无'}", ""]
        for r in results:
            md.append(fmt_card_report(r))
            md.append("")
        md.append("## v3.0 指标映射")
        md.append("```json")
        md.append(json.dumps(summary, ensure_ascii=False, indent=2))
        md.append("```")

        report = "\n".join(md)
        print(report)
        payload = {"summary": summary, "results": results, "missing": missing}
        if args.json:
            Path(args.json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"\nJSON: {args.json}")
        if args.markdown:
            Path(args.markdown).write_text(report, encoding="utf-8")
            print(f"MD:   {args.markdown}")
        sys.exit(0 if not missing and all(r["status"] == "pass" for r in results) else 1)

    # single card mode
    if not args.card_id or not args.project_dir:
        print(__doc__)
        sys.exit(2)
    if args.card_id not in CRITERIA:
        print(f"Error: unknown card {args.card_id} (expect BT-01..BT-05)", file=sys.stderr)
        sys.exit(2)

    result = score_card(args.card_id, args.project_dir, rounds=args.rounds)
    print(fmt_card_report(result))
    if args.json:
        Path(args.json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON: {args.json}")
    sys.exit(0 if result["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
