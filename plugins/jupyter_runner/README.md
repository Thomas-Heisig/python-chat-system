# 📄 Jupyter Runner Plugin

**ID:** `jupyter_runner`  
**Kategorie:** 🔧 Developer Tools  
**Status:** ✅ Implementiert

## 📝 Beschreibung

Das Jupyter Runner Plugin ermöglicht die **Ausführung von Jupyter-Notebooks** (.ipynb) direkt aus dem Chat. Es unterstützt drei Ausführungsmodi:

- **Papermill** (empfohlen) – mit Parameter-Übergabe und detaillierten Logs
- **nbconvert** – klassische Ausführung mit `jupyter nbconvert --execute`
- **Subprocess** – direkte Ausführung mit `jupyter execute`

---

## 🎯 Intent-Erkennung

Das Plugin wird durch folgende Schlüsselwörter getriggert:

```regex
\b(notebook|jupyter|ausführen|ipynb|papermill)\b
```

**Beispiele:**

- _"Führe das Notebook 'analyse.ipynb' aus."_
- _"Notebook mit Parametern ausführen."_
- _"Jupyter-Notebook ausführen."_

---

## ⚙️ Konfiguration

### Voraussetzungen

Das Plugin benötigt mindestens eine der folgenden Bibliotheken:

```bash
# Für papermill (empfohlen)
pip install papermill

# Oder für nbconvert
pip install nbconvert jupyter

# Oder für subprocess (jupyter execute)
pip install jupyter
```

### Umgebungsvariablen

Keine erforderlich.

---

## 📦 Input-Schema

```json
{
  "notebook_path": "/pfad/zu/notebook.ipynb",
  "parameters": {
    "parameter1": "Wert1",
    "parameter2": 42
  },
  "output_path": "/pfad/ausgabe.ipynb",
  "timeout": 60,
  "kernel": "python3",
  "mode": "papermill"
}
```

| Feld            | Typ     | Standard    | Beschreibung                                                 |
| --------------- | ------- | ----------- | ------------------------------------------------------------ |
| `notebook_path` | string  | –           | Pfad zur `.ipynb`-Datei (erforderlich)                       |
| `parameters`    | object  | –           | Parameter für das Notebook (nur papermill)                   |
| `output_path`   | string  | –           | Pfad für das ausgeführte Notebook (optional, temporär sonst) |
| `timeout`       | integer | `60`        | Maximale Laufzeit in Sekunden                                |
| `kernel`        | string  | `python3`   | Kernel-Name (für nbconvert/subprocess)                       |
| `mode`          | string  | `papermill` | `papermill`, `nbconvert`, `subprocess`                       |

---

## 📤 Output-Schema

```json
{
  "success": true,
  "output_notebook": "/pfad/ausgabe.ipynb",
  "logs": "Notebook erfolgreich ausgeführt. Ausgabe gespeichert unter /pfad/ausgabe.ipynb"
}
```

**Bei Fehlern:**

```json
{
  "error": "Papermill ist nicht installiert. Bitte installiere es mit 'pip install papermill'."
}
```

---

## 🧪 Beispiele

### 1. Notebook mit Parametern ausführen (Papermill)

**Input:**

```json
{
  "notebook_path": "./analyse.ipynb",
  "parameters": {
    "customer": "Heishg Naturstein",
    "data_file": "./daten.csv"
  },
  "mode": "papermill"
}
```

**Output:**

```json
{
  "success": true,
  "output_notebook": "/tmp/jupyter_output_xyz/analyse_executed.ipynb",
  "logs": "Notebook erfolgreich ausgeführt. Ausgabe gespeichert unter /tmp/jupyter_output_xyz/analyse_executed.ipynb"
}
```

### 2. Notebook mit nbconvert ausführen

**Input:**

```json
{
  "notebook_path": "./bericht.ipynb",
  "kernel": "python3",
  "mode": "nbconvert"
}
```

### 3. Subprocess-Modus

**Input:**

```json
{
  "notebook_path": "./modell.ipynb",
  "kernel": "ir",
  "mode": "subprocess"
}
```

---

## 📁 Datei-Struktur

```
packages/plugins/jupyter_runner/
├── __init__.py
├── plugin.py          # Haupt-Plugin-Code
├── __pycache__/       # Python-Cache
└── README.md          # Diese Datei
```

---

## 🔧 Fehlerbehebung

### Fehler: "Papermill ist nicht installiert"

**Lösung:**

```bash
pip install papermill
```

### Fehler: "nbconvert fehlgeschlagen"

**Lösung:** Prüfe, ob das Notebook syntaktisch korrekt ist und alle Abhängigkeiten installiert sind.

### Fehler: "Zeitüberschreitung"

**Lösung:** Erhöhe den Timeout-Wert oder optimiere das Notebook.

---

## 📝 Verwendung im Chat

**Beispiel-Chat:**

> **Nutzer:** _"Führe das Notebook 'analyse_kunden.ipynb' mit dem Parameter 'customer=Heishg Naturstein' aus."_
>
> **Elisa:** _"✅ Notebook wurde erfolgreich ausgeführt. Ausgabe gespeichert unter '...'."_

---

## 📚 Siehe auch

- [Papermill Dokumentation](https://papermill.readthedocs.io/)
- [Jupyter nbconvert](https://nbconvert.readthedocs.io/)
- [Plugins Übersicht](../PLUGINS.md)

---

**Letzte Aktualisierung:** 2026-06-28
