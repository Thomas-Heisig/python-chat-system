# packages/plugins/jupyter_runner/plugin.py
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from typing import Any, cast

PLUGIN_META: dict[str, Any] = {
    "id": "jupyter_runner",
    "name": "Jupyter Runner",
    "description": "Führt Jupyter-Notebooks aus (unterstützt Parameter und verschiedene Kernel)",
    "category": "🔧 Developer Tools",
    "apiKeyRequired": False,
    "intentPattern": r"\b(notebook|jupyter|ausführen|ipynb|papermill)\b",
    "status": "implemented",
    "settingsFields": [],
}


class JupyterRunnerPlugin:
    name = "jupyter_runner"
    description = "Führt Jupyter-Notebooks aus (unterstützt Parameter und verschiedene Kernel)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "notebook_path": {
                "type": "string",
                "description": "Pfad zur .ipynb-Datei, die ausgeführt werden soll.",
            },
            "parameters": {
                "type": "object",
                "description": "Parameter, die an das Notebook übergeben werden (wenn papermill verwendet wird).",
                "additionalProperties": True,
            },
            "output_path": {
                "type": "string",
                "description": "Pfad, unter dem das ausgeführte Notebook gespeichert werden soll (optional).",
            },
            "timeout": {
                "type": "integer",
                "default": 60,
                "description": "Maximale Laufzeit in Sekunden.",
            },
            "kernel": {
                "type": "string",
                "description": "Kernel-Name (z.B. 'python3', 'ir', 'julia-1.8'). Nur für nbconvert.",
                "default": "python3",
            },
            "mode": {
                "type": "string",
                "enum": ["papermill", "nbconvert", "subprocess"],
                "default": "papermill",
                "description": "Ausführungsmodus: papermill (empfohlen), nbconvert oder subprocess.",
            },
        },
        "required": ["notebook_path"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "output_notebook": {"type": "string"},
            "logs": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self._papermill_available = self._check_papermill()
        self._nbconvert_available = self._check_nbconvert()

    def _check_papermill(self) -> bool:
        """Prüft, ob papermill installiert ist."""
        try:
            import papermill  # type: ignore[reportMissingImports]  # noqa: F401
            return True
        except ImportError:
            return False

    def _check_nbconvert(self) -> bool:
        """Prüft, ob nbconvert installiert ist."""
        try:
            import nbconvert  # type: ignore[reportMissingImports]  # noqa: F401
            return True
        except ImportError:
            return False

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        notebook_path = str(input_data.get("notebook_path", "")).strip()
        if not notebook_path:
            return {"error": "notebook_path ist erforderlich."}

        if not os.path.exists(notebook_path):
            return {"error": f"Notebook-Datei '{notebook_path}' nicht gefunden."}

        if not notebook_path.endswith(".ipynb"):
            return {"error": "Die Datei muss eine .ipynb-Datei sein."}

        parameters_raw = input_data.get("parameters", {})
        parameters: dict[str, Any] = cast(dict[str, Any], parameters_raw) if isinstance(parameters_raw, dict) else {}
        output_path = str(input_data.get("output_path", "")).strip() or None
        timeout = max(1, int(input_data.get("timeout", 60)))
        kernel = str(input_data.get("kernel", "python3")).strip()
        mode = str(input_data.get("mode", "papermill")).lower()

        # Wenn kein Ausgabepfad angegeben ist, erstelle einen temporären
        if not output_path:
            temp_dir = tempfile.mkdtemp(prefix="jupyter_output_")
            output_path = os.path.join(temp_dir, os.path.basename(notebook_path))
            output_path = output_path.replace(".ipynb", "_executed.ipynb")

        # Modus-Auswahl
        if mode == "papermill":
            if not self._papermill_available:
                return {"error": "Papermill ist nicht installiert. Bitte installiere es mit 'pip install papermill'."}
            return await self._run_with_papermill(notebook_path, output_path, parameters, timeout)

        elif mode == "nbconvert":
            if not self._nbconvert_available:
                return {"error": "Nbconvert ist nicht installiert. Bitte installiere es mit 'pip install nbconvert'."}
            return await self._run_with_nbconvert(notebook_path, output_path, kernel, timeout)

        elif mode == "subprocess":
            return await self._run_with_subprocess(notebook_path, output_path, kernel, timeout)

        else:
            return {"error": f"Unbekannter Modus: {mode}"}

    async def _run_with_papermill(
        self,
        notebook_path: str,
        output_path: str,
        parameters: dict[str, Any],
        timeout: int,
    ) -> dict[str, Any]:
        """Führt das Notebook mit papermill aus."""
        try:
            import papermill as pm  # type: ignore[reportMissingImports]
        except ImportError:
            return {"error": "Papermill ist nicht installiert."}

        try:
            # Papermill-Ausführung (blockiert)
            execute_notebook = getattr(pm, "execute_notebook", None)
            if not callable(execute_notebook):
                return {"error": "Papermill-Funktion execute_notebook nicht verfügbar."}

            execute_notebook(
                notebook_path,
                output_path,
                parameters=parameters,
                progress_bar=False,
            )
            # Ergebnis ist ein Notebook-Objekt, wir geben den Pfad zurück
            return {
                "success": True,
                "output_notebook": output_path,
                "logs": f"Notebook erfolgreich ausgeführt. Ausgabe gespeichert unter {output_path}",
            }
        except Exception as e:
            return {"error": f"Fehler bei der Ausführung mit papermill: {str(e)}"}

    async def _run_with_nbconvert(
        self,
        notebook_path: str,
        output_path: str,
        kernel: str,
        timeout: int,
    ) -> dict[str, Any]:
        """Führt das Notebook mit nbconvert aus (keine Parameter-Unterstützung)."""
        # nbconvert kann Notebooks ausführen, aber ohne Parameter
        # Wir nutzen den Befehl: jupyter nbconvert --to notebook --execute --output output_path notebook.ipynb
        try:
            import nbconvert  # type: ignore[reportMissingImports]  # noqa: F401
        except ImportError:
            return {"error": "nbconvert ist nicht installiert."}

        # Wir müssen den Befehl mit subprocess ausführen, da nbconvert keine direkte API für Ausführung hat
        cmd = [
            "jupyter",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            "--output",
            output_path,
            notebook_path,
        ]
        if kernel:
            cmd.extend(["--ExecutePreprocessor.kernel_name", kernel])

        process: asyncio.subprocess.Process | None = None
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            if process.returncode != 0:
                return {"error": f"nbconvert fehlgeschlagen: {stderr.decode('utf-8')}"}
            return {
                "success": True,
                "output_notebook": output_path,
                "logs": stdout.decode("utf-8") or "Notebook erfolgreich ausgeführt.",
            }
        except asyncio.TimeoutError:
            if process is not None:
                process.kill()
            return {"error": f"Zeitüberschreitung ({timeout} Sekunden) bei der Ausführung."}
        except Exception as e:
            return {"error": f"Fehler bei nbconvert: {str(e)}"}

    async def _run_with_subprocess(
        self,
        notebook_path: str,
        output_path: str,
        kernel: str,
        timeout: int,
    ) -> dict[str, Any]:
        """Führt das Notebook mit subprocess und jupyter execute aus (keine Parameter)."""
        cmd = [
            sys.executable,
            "-m",
            "jupyter",
            "execute",
            "--kernel",
            kernel,
            "--output",
            output_path,
            notebook_path,
        ]
        process: asyncio.subprocess.Process | None = None
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            if process.returncode != 0:
                return {"error": f"Ausführung fehlgeschlagen: {stderr.decode('utf-8')}"}
            return {
                "success": True,
                "output_notebook": output_path,
                "logs": stdout.decode("utf-8") or "Notebook erfolgreich ausgeführt.",
            }
        except asyncio.TimeoutError:
            if process is not None:
                process.kill()
            return {"error": f"Zeitüberschreitung ({timeout} Sekunden) bei der Ausführung."}
        except Exception as e:
            return {"error": f"Fehler bei subprocess: {str(e)}"}


