"""Wrappers around pinned Google WFF validator and memory evaluator releases."""

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = PROJECT_ROOT / "vendor" / "google-watchface" / "tools"
VALIDATOR_JAR = TOOLS_DIR / "wff-validator.jar"
MEMORY_JAR = TOOLS_DIR / "memory-footprint.jar"


def _java() -> Optional[str]:
    configured = os.getenv("WFF_JAVA", "/opt/temurin-17/bin/java")
    if Path(configured).is_file():
        return configured
    return shutil.which("java")


def validate_with_official_tool(xml_bytes: bytes, version: int = 1) -> List[dict]:
    java = _java()
    if not java or not VALIDATOR_JAR.is_file():
        return [{
            "source": "official_validator", "rule": "TOOL_UNAVAILABLE", "severity": "warning",
            "element": None, "line": None,
            "message": "Google WFF validator 运行时不可用",
            "hint": "配置 WFF_JAVA 并部署 vendor/google-watchface/tools/wff-validator.jar",
        }]
    xml_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as handle:
            handle.write(xml_bytes)
            xml_path = Path(handle.name)
        process = subprocess.run(
            [java, "-jar", str(VALIDATOR_JAR), str(version), str(xml_path)],
            capture_output=True, text=True, timeout=10,
        )
        output = "\n".join(part for part in (process.stdout, process.stderr) if part)
        if "PASSED" in output and "FAILED" not in output and "SEVERE:" not in output:
            return []
        issues = []
        for raw_line in output.splitlines():
            if "SEVERE:" not in raw_line:
                continue
            match = re.search(r"\[Line (\d+):Column \d+\]:\s*(.*)$", raw_line)
            issues.append({
                "source": "official_validator", "rule": "GOOGLE_VALIDATOR", "severity": "error",
                "element": None, "line": int(match.group(1)) if match else None,
                "message": match.group(2) if match else raw_line.split("SEVERE:", 1)[-1].strip(),
                "hint": "按 Google WFF validator 1.7.0 的错误修正 XML",
            })
        if issues:
            return issues
        return [{
            "source": "official_validator", "rule": "TOOL_FAILED", "severity": "error",
            "element": None, "line": None,
            "message": output.strip() or f"validator exited with {process.returncode}",
            "hint": "检查官方 validator 运行时和输入文件",
        }]
    except subprocess.TimeoutExpired:
        return [{
            "source": "official_validator", "rule": "TOOL_TIMEOUT", "severity": "error",
            "element": None, "line": None, "message": "Google WFF validator 超过 10 秒",
            "hint": "精简 XML 或检查 Java 运行时",
        }]
    finally:
        if xml_path is not None:
            xml_path.unlink(missing_ok=True)


def evaluate_memory(apk_path: Path, version: int = 1) -> dict:
    java = _java()
    if not java or not MEMORY_JAR.is_file():
        return {"source": "unavailable", "warning": "Google memory-footprint 运行时不可用"}
    try:
        process = subprocess.run(
            [java, "-jar", str(MEMORY_JAR), "--watch-face", str(apk_path),
             "--schema-version", str(version), "--report"],
            capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        return {"source": "official", "warning": "Google memory-footprint 超过 30 秒"}
    output = (process.stdout or "").strip()
    try:
        report = json.loads(output[output.index("{"):])
    except (ValueError, json.JSONDecodeError):
        return {
            "source": "official", "warning": (process.stderr or output or "memory evaluator failed").strip(),
        }
    return {
        "source": "official",
        "total_bytes": report.get("totalBytes"),
        "max_active_bytes": report.get("maxActiveBytes"),
        "max_ambient_bytes": report.get("maxAmbientBytes"),
    }
