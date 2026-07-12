#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FRONTEND_ROOT="${PROJECT_ROOT}/frontend"

BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
STOP_EXISTING="${STOP_EXISTING:-0}"

resolve_backend_python() {
  local candidates=(
    "${PROJECT_ROOT}/.venv-chat/bin/python"
    "${PROJECT_ROOT}/.venv-training/bin/python"
    "${PROJECT_ROOT}/.venv/bin/python"
  )

  for candidate in "${candidates[@]}"; do
    if [[ -x "${candidate}" ]]; then
      echo "${candidate}"
      return 0
    fi
  done

  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi

  echo ""
  return 1
}

BACKEND_PYTHON="$(resolve_backend_python || true)"
if [[ -z "${BACKEND_PYTHON}" ]]; then
  echo "python is required but not installed (expected .venv-chat/.venv-training/.venv or global python)."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required but not installed."
  exit 1
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "npx is required but not installed."
  exit 1
fi

port_in_use() {
  "${BACKEND_PYTHON}" - "$1" <<'PY'
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(0.3)
result = sock.connect_ex(("127.0.0.1", port))
sock.close()
sys.exit(0 if result == 0 else 1)
PY
}

stop_port_processes() {
  local port="$1"

  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -ti tcp:"${port}" || true)"
    if [[ -n "${pids}" ]]; then
      echo "Stopping processes on port ${port}: ${pids}"
      # shellcheck disable=SC2086
      kill -9 ${pids} >/dev/null 2>&1 || true
    fi
    return
  fi

  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}"/tcp >/dev/null 2>&1 || true
    return
  fi

  echo "WARN: STOP_EXISTING aktiv, aber weder lsof noch fuser verfuegbar; Port ${port} kann nicht automatisch freigegeben werden."
}

if [[ ! -d "${FRONTEND_ROOT}/node_modules" ]]; then
  (cd "${FRONTEND_ROOT}" && npm install)
fi

if [[ "${STOP_EXISTING}" == "1" ]]; then
  stop_port_processes "${BACKEND_PORT}"
  stop_port_processes "${FRONTEND_PORT}"

  if port_in_use "${BACKEND_PORT}" || port_in_use "${FRONTEND_PORT}"; then
    echo "Neustart abgebrochen: Backend und Frontend muessen zuerst gestoppt werden."
    exit 1
  fi
fi

BACKEND_PID=""
FRONTEND_PID=""

if port_in_use "${BACKEND_PORT}"; then
  echo "WARN: Backend-Port ${BACKEND_PORT} ist bereits belegt. Backend wird nicht erneut gestartet."
else
  "${BACKEND_PYTHON}" "${PROJECT_ROOT}/start.py" --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" --reload &
  BACKEND_PID=$!
fi

if port_in_use "${FRONTEND_PORT}"; then
  echo "WARN: Frontend-Port ${FRONTEND_PORT} ist bereits belegt. Frontend wird nicht erneut gestartet."
else
  (cd "${FRONTEND_ROOT}" && VITE_DEV_BACKEND_TARGET="http://127.0.0.1:${BACKEND_PORT}" npx vite --host "${FRONTEND_HOST}" --port "${FRONTEND_PORT}") &
  FRONTEND_PID=$!
fi

cleanup() {
  if [[ -n "${BACKEND_PID}" ]]; then
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${FRONTEND_PID}" ]]; then
    kill "${FRONTEND_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

echo "Backend:  http://localhost:${BACKEND_PORT}"
echo "Frontend: http://localhost:${FRONTEND_PORT}"

if [[ -n "${BACKEND_PID}" ]] && [[ -n "${FRONTEND_PID}" ]]; then
  wait -n "${BACKEND_PID}" "${FRONTEND_PID}"
elif [[ -n "${BACKEND_PID}" ]]; then
  wait "${BACKEND_PID}"
elif [[ -n "${FRONTEND_PID}" ]]; then
  wait "${FRONTEND_PID}"
else
  echo "Keine neuen Prozesse gestartet, da beide Ports bereits belegt sind."
fi
