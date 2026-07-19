# packages/plugins/calendar/plugin.py
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, cast

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "calendar",
    "name": "Calendar",
    "description": "Terminplanung und Kalenderverwaltung",
    "category": "📱 Social & Communication",
    "apiKeyRequired": True,
    "intentPattern": r"\b(termin|kalender|beratung|besichtigung|vorort|meeting|appointment)\b",
    "status": "implemented",
    "settingsFields": [],
}


class CalendarPlugin:
    name = "calendar"
    description = "Terminplanung und Kalenderverwaltung"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "create", "delete"],
                "default": "list",
                "description": "Aktion: list = Termine anzeigen, create = Termin erstellen, delete = Termin löschen.",
            },
            "date": {
                "type": "string",
                "description": "Datum im Format YYYY-MM-DD. Für 'list' optional (heute). Für 'create' erforderlich.",
            },
            "time": {
                "type": "string",
                "description": "Uhrzeit im Format HH:MM. Für 'create' erforderlich.",
            },
            "title": {
                "type": "string",
                "description": "Titel des Termins. Für 'create' erforderlich.",
            },
            "description": {
                "type": "string",
                "description": "Beschreibung des Termins (optional).",
            },
            "duration_minutes": {
                "type": "integer",
                "default": 60,
                "description": "Dauer in Minuten (optional).",
            },
            "event_id": {
                "type": "string",
                "description": "ID des zu löschenden Termins. Für 'delete' erforderlich.",
            },
        },
        "required": ["action"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "events": {"type": "array"},
            "event_id": {"type": "string"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        # Lokaler Speicher für Termine (in Produktion durch Datenbank ersetzen)
        self._events: List[Dict[str, Any]] = []
        self._load_events()

    def _load_events(self):
        """Lädt Termine aus lokaler JSON-Datei (falls vorhanden)."""
        storage_path = os.getenv("CALENDAR_STORAGE_PATH", "./calendar_events.json")
        try:
            if os.path.exists(storage_path):
                with open(storage_path, "r", encoding="utf-8") as f:
                    self._events = json.load(f)
        except Exception:
            self._events = []

    def _save_events(self):
        """Speichert Termine in lokaler JSON-Datei."""
        storage_path = os.getenv("CALENDAR_STORAGE_PATH", "./calendar_events.json")
        try:
            with open(storage_path, "w", encoding="utf-8") as f:
                json.dump(self._events, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        action = str(input_data.get("action", "list")).lower()
        date_str = str(input_data.get("date", "")).strip()
        time_str = str(input_data.get("time", "")).strip()
        title = str(input_data.get("title", "")).strip()
        description = str(input_data.get("description", "")).strip()
        duration = int(input_data.get("duration_minutes", 60))
        event_id = str(input_data.get("event_id", "")).strip()

        # Google Calendar Integration (optional)
        google_api_key = os.getenv("GOOGLE_CALENDAR_API_KEY", "")
        calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

        if action == "list":
            return await self._list_events(date_str, google_api_key, calendar_id)

        if action == "create":
            if not date_str or not time_str or not title:
                return {
                    "success": False,
                    "error": "Für 'create' sind date, time und title erforderlich.",
                }

            if google_api_key:
                # Google Calendar API nutzen
                return await self._create_google_event(
                    date_str, time_str, title, description, duration, google_api_key, calendar_id
                )
            else:
                # Lokale Speicherung
                return self._create_local_event(date_str, time_str, title, description, duration)

        if action == "delete":
            if not event_id:
                return {"success": False, "error": "Für 'delete' ist event_id erforderlich."}

            if google_api_key:
                return await self._delete_google_event(event_id, google_api_key, calendar_id)
            else:
                return self._delete_local_event(event_id)

        return {"success": False, "error": f"Unbekannte Aktion: {action}"}

    async def _list_events(
        self, date_str: str, google_api_key: str = "", calendar_id: str = "primary"
    ) -> dict[str, Any]:
        """Listet Termine für einen bestimmten Tag oder heute."""
        try:
            if date_str:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            else:
                target_date = datetime.now().date()
        except ValueError:
            return {"success": False, "error": "Ungültiges Datumsformat. Verwende YYYY-MM-DD."}

        if google_api_key:
            # Google Calendar API
            return await self._list_google_events(target_date, google_api_key, calendar_id)
        else:
            # Lokale Termine
            return self._list_local_events(target_date)

    def _list_local_events(self, target_date: datetime.date) -> dict[str, Any]:
        """Listet lokale Termine."""
        events = []
        for event in self._events:
            try:
                event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
                if event_date == target_date:
                    events.append(event)
            except Exception:
                continue

        if not events:
            return {
                "success": True,
                "message": f"Keine Termine für {target_date.isoformat()}.",
                "events": [],
            }

        return {
            "success": True,
            "message": f"{len(events)} Termin(e) für {target_date.isoformat()}:",
            "events": events,
        }

    async def _list_google_events(
        self, target_date: datetime.date, api_key: str, calendar_id: str
    ) -> dict[str, Any]:
        """Listet Google Calendar Termine."""
        time_min = datetime.combine(target_date, datetime.min.time()).isoformat() + "Z"
        time_max = datetime.combine(target_date, datetime.max.time()).isoformat() + "Z"

        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
        params = {
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": "true",
            "orderBy": "startTime",
            "key": api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {"success": False, "error": "Kalender nicht gefunden. Prüfe GOOGLE_CALENDAR_ID."}
            if e.response.status_code == 403:
                return {"success": False, "error": "API-Key ungültig oder keine Berechtigung."}
            return {"success": False, "error": f"HTTP-Fehler: {e.response.status_code}"}
        except Exception as e:
            return {"success": False, "error": f"Fehler: {str(e)}"}

        events = []
        items = data.get("items", [])
        for item in items:
            start = item.get("start", {})
            start_time = start.get("dateTime") or start.get("date")
            events.append({
                "id": item.get("id"),
                "title": item.get("summary", "Ohne Titel"),
                "start_time": start_time,
                "end_time": item.get("end", {}).get("dateTime") or item.get("end", {}).get("date"),
                "description": item.get("description", ""),
            })

        if not events:
            return {
                "success": True,
                "message": f"Keine Google Calendar Termine für {target_date.isoformat()}.",
                "events": [],
            }

        return {
            "success": True,
            "message": f"{len(events)} Termin(e) für {target_date.isoformat()}:",
            "events": events,
        }

    def _create_local_event(
        self, date_str: str, time_str: str, title: str, description: str, duration: int
    ) -> dict[str, Any]:
        """Erstellt einen lokalen Termin."""
        try:
            # Datum und Uhrzeit validieren
            datetime.strptime(date_str, "%Y-%m-%d")
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            return {"success": False, "error": "Ungültiges Datum oder Uhrzeit. Verwende YYYY-MM-DD und HH:MM."}

        event = {
            "id": f"local_{datetime.now().timestamp()}",
            "date": date_str,
            "time": time_str,
            "title": title,
            "description": description,
            "duration_minutes": duration,
            "created_at": datetime.now().isoformat(),
        }

        self._events.append(event)
        self._save_events()

        return {
            "success": True,
            "message": f"Termin '{title}' am {date_str} um {time_str} erstellt.",
            "event_id": event["id"],
            "event": event,
        }

    async def _create_google_event(
        self, date_str: str, time_str: str, title: str, description: str, duration: int, api_key: str, calendar_id: str
    ) -> dict[str, Any]:
        """Erstellt einen Google Calendar Termin (benötigt OAuth2-Token)."""
        # Hinweis: Für Google Calendar benötigt man OAuth2, keinen API-Key.
        # Diese Implementierung ist ein Platzhalter für die Integration.
        # In der Praxis müsste ein OAuth2-Token (Access Token) verwendet werden.
        return {
            "success": False,
            "error": "Google Calendar-Erstellung benötigt OAuth2. Bitte konfiguriere GOOGLE_OAUTH_CLIENT_ID und -SECRET.",
        }

    def _delete_local_event(self, event_id: str) -> dict[str, Any]:
        """Löscht einen lokalen Termin."""
        for i, event in enumerate(self._events):
            if event.get("id") == event_id:
                del self._events[i]
                self._save_events()
                return {
                    "success": True,
                    "message": f"Termin {event_id} gelöscht.",
                }

        return {"success": False, "error": f"Termin mit ID {event_id} nicht gefunden."}

    async def _delete_google_event(self, event_id: str, api_key: str, calendar_id: str) -> dict[str, Any]:
        """Löscht einen Google Calendar Termin (benötigt OAuth2)."""
        # Hinweis: Auch hier ist OAuth2 erforderlich.
        return {
            "success": False,
            "error": "Google Calendar-Löschung benötigt OAuth2. Bitte konfiguriere GOOGLE_OAUTH_CLIENT_ID und -SECRET.",
        }

