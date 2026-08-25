#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="/tmp/watchface-forge"
PID_DIR="$RUNTIME_DIR/pids"
LOG_DIR="$RUNTIME_DIR/logs"

mkdir -p "$PID_DIR" "$LOG_DIR"

# Local secrets/config are intentionally untracked. Export entries so uvicorn,
# Celery and Next inherit the same runtime configuration after container restart.
if test -f "$PROJECT_DIR/.env"; then
  set -a
  # shellcheck disable=SC1091
  source "$PROJECT_DIR/.env"
  set +a
fi

is_running() {
  local name="$1"
  local pid_file="$PID_DIR/$name.pid"
  test -f "$pid_file" && kill -0 "$(cat "$pid_file")" 2>/dev/null
}

find_existing_pid() {
  case "$1" in
    celery) pgrep -f '^python3 -m celery -A api.tasks worker' | head -1 || true ;;
    api) pgrep -f '^python3 -m uvicorn api.app:app' | head -1 || true ;;
    web) pgrep -f '^next-server' | head -1 || true ;;
  esac
}

start_process() {
  local name="$1"
  shift
  if ! is_running "$name"; then
    local existing_pid
    existing_pid="$(find_existing_pid "$name")"
    if test -n "$existing_pid"; then
      echo "$existing_pid" >"$PID_DIR/$name.pid"
    fi
  fi
  if is_running "$name"; then
    echo "$name: already running (PID $(cat "$PID_DIR/$name.pid"))"
    return
  fi
  (
    cd "$PROJECT_DIR"
    nohup setsid "$@" >"$LOG_DIR/$name.log" 2>&1 &
    echo $! >"$PID_DIR/$name.pid"
  )
  sleep 1
  if ! is_running "$name"; then
    echo "$name: failed to start" >&2
    tail -40 "$LOG_DIR/$name.log" >&2 || true
    exit 1
  fi
  echo "$name: started (PID $(cat "$PID_DIR/$name.pid"))"
}

wait_http() {
  local name="$1"
  local url="$2"
  local attempts=20
  while (( attempts > 0 )); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "$name: ready ($url)"
      return
    fi
    attempts=$((attempts - 1))
    sleep 1
  done
  echo "$name: did not become ready" >&2
  tail -40 "$LOG_DIR/$name.log" >&2 || true
  exit 1
}

start_all() {
  cd "$PROJECT_DIR"

  if redis-cli ping >/dev/null 2>&1; then
    echo "redis: already running"
  else
    redis-server --daemonize yes --logfile "$LOG_DIR/redis.log"
    redis-cli ping >/dev/null
    echo "redis: started"
  fi

  start_process celery python3 -m celery -A api.tasks worker -Q image,default -c 2 --loglevel WARNING
  start_process api python3 -m uvicorn api.app:app --host 0.0.0.0 --port 8000
  wait_http api http://127.0.0.1:8000/api/health

  if ! test -f "$PROJECT_DIR/web/.next/BUILD_ID"; then
    echo "web: production build missing, building..."
    (cd "$PROJECT_DIR/web" && npm run build)
  fi
  if ! is_running web; then
    (
      cd "$PROJECT_DIR/web"
      nohup setsid npm run start >"$LOG_DIR/web.log" 2>&1 &
      echo $! >"$PID_DIR/web.pid"
    )
    sleep 1
    echo "web: started (PID $(cat "$PID_DIR/web.pid"))"
  else
    echo "web: already running (PID $(cat "$PID_DIR/web.pid"))"
  fi
  wait_http web http://127.0.0.1:3000/editor
}

stop_one() {
  local name="$1"
  local pid_file="$PID_DIR/$name.pid"
  if ! is_running "$name"; then
    local existing_pid
    existing_pid="$(find_existing_pid "$name")"
    if test -n "$existing_pid"; then
      echo "$existing_pid" >"$pid_file"
    fi
  fi
  if is_running "$name"; then
    local pid
    pid="$(cat "$pid_file")"
    kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
    for _ in 1 2 3 4 5; do
      kill -0 "$pid" 2>/dev/null || break
      sleep 1
    done
    kill -9 -- "-$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
    echo "$name: stopped"
  else
    echo "$name: not running"
  fi
  rm -f "$pid_file"
}

stop_all() {
  stop_one web
  stop_one api
  stop_one celery
  if redis-cli ping >/dev/null 2>&1; then
    redis-cli shutdown nosave >/dev/null 2>&1 || true
    echo "redis: stopped"
  else
    echo "redis: not running"
  fi
}

status_all() {
  local existing_pid
  if redis-cli ping >/dev/null 2>&1; then echo "redis: running"; else echo "redis: stopped"; fi
  for name in celery api web; do
    if ! is_running "$name"; then
      existing_pid="$(find_existing_pid "$name")"
      if test -n "$existing_pid"; then echo "$existing_pid" >"$PID_DIR/$name.pid"; fi
    fi
    if is_running "$name"; then
      echo "$name: running (PID $(cat "$PID_DIR/$name.pid"))"
    else
      echo "$name: stopped"
    fi
  done
  echo "logs: $LOG_DIR"
}

case "${1:-start}" in
  start) start_all ;;
  stop) stop_all ;;
  restart) stop_all; start_all ;;
  status) status_all ;;
  *) echo "Usage: $0 {start|stop|restart|status}" >&2; exit 2 ;;
esac
