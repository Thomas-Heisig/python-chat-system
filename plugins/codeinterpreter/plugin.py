# packages/plugins/codeinterpreter/plugin.py
from __future__ import annotations

import asyncio
import os
import re
import subprocess
import sys
import tempfile
import time
from typing import Any

PLUGIN_META: dict[str, Any] = {
    "id": "codeinterpreter",
    "name": "Code Interpreter",
    "description": "Führt Python-Code in einer Sandbox aus (mit Zeitlimit und Sicherheitsbeschränkungen)",
    "category": "🔧 Developer Tools",
    "apiKeyRequired": False,
    "intentPattern": r"```python|code|python|ausführen",
    "status": "implemented",
    "settingsFields": [],
}

class CodeInterpreterPlugin:
    name = "codeinterpreter"
    description = "Führt Python-Code in einer Sandbox aus (mit Zeitlimit und Sicherheitsbeschränkungen)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Der auszuführende Python-Code. Kann auch einen Markdown-Codeblock enthalten.",
            },
            "timeout": {
                "type": "integer",
                "default": 10,
                "description": "Maximale Laufzeit in Sekunden.",
            },
            "sandbox_mode": {
                "type": "string",
                "enum": ["local", "docker"],
                "default": "local",
                "description": "Sandbox-Modus: lokal (direkt im temporären Verzeichnis) oder Docker (isoliert).",
            },
        },
        "required": ["code"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "output": {"type": "string"},
            "error": {"type": "string"},
            "duration_ms": {"type": "number"},
        },
    }

    def __init__(self):
        self._docker_available = self._check_docker_available()

    @staticmethod
    def _check_docker_available() -> bool:
        """Prüft, ob Docker installiert und erreichbar ist."""
        try:
            result = subprocess.run(
                ["docker", "version", "--format", "{{.Server.Version}}"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def _extract_code(text: str) -> str:
        """Extrahiert Python-Code aus einer möglichen Markdown-Codeblock."""
        # Suche nach ```python ... ``` Block
        match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Fallback: gesamter Text wird als Code interpretiert
        return text.strip()

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        raw_code = str(input_data.get("code", "")).strip()
        if not raw_code:
            return {"error": "Kein Code angegeben."}

        code = self._extract_code(raw_code)
        if not code:
            return {"error": "Kein gültiger Python-Code gefunden."}

        timeout = max(1, int(input_data.get("timeout", 10)))
        sandbox_mode = str(input_data.get("sandbox_mode", "local")).lower()

        start_time = time.perf_counter()

        try:
            if sandbox_mode == "docker" and self._docker_available:
                output = await self._run_in_docker(code, timeout)
            else:
                output = await self._run_local_sandbox(code, timeout)

            duration_ms = (time.perf_counter() - start_time) * 1000

            return {
                "output": output,
                "duration_ms": round(duration_ms, 2),
            }

        except subprocess.TimeoutExpired:
            return {"error": f"Zeitüberschreitung ({timeout} Sekunden)."}
        except Exception as e:
            return {"error": f"Fehler: {str(e)}"}

    async def _run_local_sandbox(self, code: str, timeout: int) -> str:
        """Führt Code in einem temporären Verzeichnis lokal aus (mit Zeitlimit)."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self._run_local_sandbox_sync,
            code,
            timeout,
        )

    def _run_local_sandbox_sync(self, code: str, timeout: int) -> str:
        """Synchroner Teil der lokalen Sandbox."""
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, "script.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)

            # Python-Prozess starten
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=tmpdir,
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                raise

            if process.returncode != 0:
                error_msg = stderr.strip() or f"Fehler beim Ausführen des Codes (Exit-Code {process.returncode})."
                return f"⚠️ Fehler:\n{error_msg}"

            return stdout.strip() or "Code erfolgreich ausgeführt (keine Ausgabe)."

    async def _run_in_docker(self, code: str, timeout: int) -> str:
        """Führt Code in einem Docker-Container aus (isoliert)."""
        if not self._docker_available:
            return "Docker ist nicht verfügbar. Führe Code lokal aus."

        # Docker-Image: Standard python-slim
        image = os.getenv("CODE_SANDBOX_IMAGE", "python:3.11-slim")

        # Code in eine Datei schreiben
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            script_path = f.name

        try:
            # Docker-Befehl: Container mit Zeitlimit, kein Netzwerk, Memory-Limit
            docker_cmd = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--memory",
                "256m",
                "--cpus",
                "0.5",
                "--ulimit",
                "cpu",
                str(timeout),
                "-v",
                f"{script_path}:/app/script.py",
                image,
                "python",
                "/app/script.py",
            ]

            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout + 5,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                raise subprocess.TimeoutExpired(cmd="docker", timeout=timeout)

            output = stdout.decode("utf-8").strip()
            error = stderr.decode("utf-8").strip()

            if process.returncode != 0:
                error_msg = error or f"Fehler (Exit-Code {process.returncode})."
                return f"⚠️ Fehler:\n{error_msg}"

            return output or "Code erfolgreich ausgeführt (keine Ausgabe)."

        finally:
            os.unlink(script_path)


