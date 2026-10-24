#!/usr/bin/env bash
# check-upstream: 比对 google/watchface 上游 HEAD 与 vendor 钉定 commit (REPAIR_PLAN P3)
# 用法: bash tools/check-upstream.sh   — 边界相关会话必跑 (skill 更新三触发器之一)
# 退出码: 0=一致  1=上游有更新(需重跑 vendor 升级流程)  2=网络/API 失败(手动核查)
set -uo pipefail
cd "$(dirname "$0")/.."

PINNED=$(grep -oE 'Commit: `[0-9a-f]{40}`' vendor/google-watchface/SOURCE.md | head -1 | grep -oE '[0-9a-f]{40}')
if [ -z "$PINNED" ]; then echo "✗ 无法从 SOURCE.md 解析钉定 commit"; exit 2; fi

LATEST=$(curl -sS --max-time 30 "https://api.github.com/repos/google/watchface/commits?per_page=1" \
  | python3 -c "import json,sys
try:
    print(json.load(sys.stdin)[0]['sha'])
except Exception:
    print('')" 2>/dev/null)
if [ -z "$LATEST" ]; then echo "✗ 上游查询失败 (网络/GitHub API 限额) — 请手动核查"; exit 2; fi

echo "钉定: $PINNED"
echo "上游: $LATEST"
if [ "$PINNED" = "$LATEST" ]; then
  echo "✓ 一致，无需动作"
  exit 0
else
  echo "⚠ 上游有新提交 → 重跑 vendor 升级流程 (specification 树 + SOURCE.md + release 资产 SHA 核对) 并回灌知识层"
  exit 1
fi
