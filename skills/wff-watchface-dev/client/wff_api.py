#!/usr/bin/env python3
"""WFF API Client — validate/preview/build watchfaces via platform HTTP API.

Two modes:
  - remote: HTTP to platform API (needs base_url + api_key)
  - local:  subprocess to wff-builder CLI (no platform dependency)

Usage:
  python wff_api.py validate <project_dir>
  python wff_api.py preview  <project_dir> [--times "10:08,23:59"] [--modes active,ambient]
  python wff_api.py build    <project_dir>
  python wff_api.py status                     # check platform availability
"""
import argparse
import base64
import json
import os
import subprocess
import sys
from pathlib import Path

# --- Config ---
CONFIG_FILE = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "base_url": "",           # e.g. "https://watchface.example.com/api/v1"
    "api_key": "",            # X-API-Key
    "mode": "local",          # "remote" or "local"
    "wff_builder": str(Path(__file__).parents[3] / "wff-builder" / "wff_builder.py"),
    "timeout": 60,
}


def load_config():
    if CONFIG_FILE.exists():
        cfg = json.loads(CONFIG_FILE.read_text())
        merged = {**DEFAULT_CONFIG, **cfg}
        return merged
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


# --- Local mode (subprocess to wff-builder) ---
def local_validate(project_dir, cfg):
    return _local_run(["validate", project_dir], cfg)


def local_build(project_dir, cfg):
    return _local_run(["build", project_dir], cfg)


def local_preview(project_dir, cfg, times=None, modes=None):
    """Local preview: not yet implemented (platform provides renderer)."""
    return {
        "status": "not_implemented",
        "message": "Preview requires platform API. Use remote mode or wait for Phase 4A."
    }


def _local_run(args, cfg):
    cmd = [sys.executable, cfg["wff_builder"]] + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=cfg.get("timeout", 60)
        )
        return {
            "status": "success" if result.returncode == 0 else "error",
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": f"Timed out after {cfg.get('timeout', 60)}s"}
    except FileNotFoundError:
        return {"status": "error", "error": f"wff_builder.py not found at {cfg['wff_builder']}"}


# --- Remote mode (HTTP to platform API) ---
def remote_request(endpoint, cfg, method="POST", files=None, data=None):
    try:
        import httpx
    except ImportError:
        return {"status": "error", "error": "httpx not installed. Run: pip install httpx"}

    url = f"{cfg['base_url']}/{endpoint}"
    headers = {"X-API-Key": cfg["api_key"]}
    try:
        with httpx.Client(timeout=cfg.get("timeout", 60)) as client:
            if method == "POST":
                resp = client.post(url, headers=headers, files=files, data=data)
            else:
                resp = client.get(url, headers=headers)
        if resp.status_code in (200, 202):
            return resp.json()
        else:
            return {
                "status": "error",
                "http_status": resp.status_code,
                "error": resp.text[:500]
            }
    except httpx.RequestError as e:
        return {"status": "error", "error": f"Request failed: {e}"}


def remote_validate(project_dir, cfg):
    files = _collect_files(project_dir)
    if not files:
        return {"status": "error", "error": "No watchface.xml found"}
    return remote_request("wff/validate", cfg, files=files)


def remote_preview(project_dir, cfg, times=None, modes=None):
    files = _collect_files(project_dir)
    data = {}
    if times:
        data["times"] = times
    if modes:
        data["modes"] = modes
    return remote_request("wff/preview", cfg, files=files, data=data)


def remote_build(project_dir, cfg):
    files = _collect_files(project_dir)
    data = {
        "name": Path(project_dir).name,
        "package_name": f"com.watchfaceforge.{Path(project_dir).name}",
        "version_code": "1",
    }
    return remote_request("wff/build", cfg, files=files, data=data)


def _collect_files(project_dir):
    """Collect watchface.xml + project.yaml + res/ into multipart files."""
    project_dir = Path(project_dir)
    files = {}
    xml = project_dir / "watchface.xml"
    if not xml.exists():
        return None
    files["xml"] = ("watchface.xml", xml.read_bytes(), "text/xml")
    yaml = project_dir / "project.yaml"
    if yaml.exists():
        files["project"] = ("project.yaml", yaml.read_bytes(), "text/yaml")
    # Collect res/ files
    res = project_dir / "res"
    if res.exists():
        for f in res.rglob("*"):
            if f.is_file():
                rel = str(f.relative_to(res))
                files[f"asset_{rel}"] = (rel, f.read_bytes(), "application/octet-stream")
    return files


def remote_status(cfg):
    """Check platform availability."""
    try:
        import httpx
    except ImportError:
        return {"status": "error", "error": "httpx not installed"}
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(f"{cfg['base_url']}/health")
            return resp.json()
    except httpx.RequestError as e:
        return {"status": "unreachable", "error": str(e)}


# --- CLI ---
def main():
    parser = argparse.ArgumentParser(description="WFF API Client")
    parser.add_argument("command", choices=["validate", "preview", "build", "status", "config"])
    parser.add_argument("project_dir", nargs="?", help="Project directory")
    parser.add_argument("--times", default="10:08,23:59", help="Preview times")
    parser.add_argument("--modes", default="active,ambient", help="Preview modes")
    parser.add_argument("--remote", action="store_true", help="Force remote mode")
    parser.add_argument("--local", action="store_true", help="Force local mode")
    args = parser.parse_args()

    cfg = load_config()

    # Mode override
    if args.remote:
        cfg["mode"] = "remote"
    elif args.local:
        cfg["mode"] = "local"

    is_remote = cfg["mode"] == "remote" and cfg.get("base_url")

    if args.command == "status":
        if is_remote:
            result = remote_status(cfg)
        else:
            result = {"status": "local_mode", "wff_builder": cfg["wff_builder"]}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if args.command == "config":
        safe = {k: v for k, v in cfg.items() if k != "api_key"}
        print(json.dumps(safe, indent=2, ensure_ascii=False))
        return

    if not args.project_dir:
        print("Error: project_dir required", file=sys.stderr)
        sys.exit(1)

    if args.command == "validate":
        result = remote_validate(args.project_dir, cfg) if is_remote else local_validate(args.project_dir, cfg)
    elif args.command == "preview":
        if is_remote:
            result = remote_preview(args.project_dir, cfg, args.times, args.modes)
        else:
            result = local_preview(args.project_dir, cfg, args.times, args.modes)
    elif args.command == "build":
        result = remote_build(args.project_dir, cfg) if is_remote else local_build(args.project_dir, cfg)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit code
    if isinstance(result, dict) and result.get("status") == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
