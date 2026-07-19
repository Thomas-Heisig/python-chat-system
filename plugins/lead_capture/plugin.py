# packages/plugins/lead_capture/plugin.py
from __future__ import annotations
# pyright: reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownLambdaType=false

import json
import os
from datetime import datetime, timezone
from typing import Any


PLUGIN_META: dict[str, Any] = {
    "id": "lead_capture",
    "name": "Lead Capture",
    "description": "Kundenkontakte speichern (Lead-Erfassung für Vertrieb und CRM)",
    "category": "📱 Social & Communication",
    "apiKeyRequired": False,
    "intentPattern": r"\b(kontakt|adresse|telefon|email|lead|anfrage|interessent|kunde|beratung|termin|besichtigung)\b",
    "status": "implemented",
    "settingsFields": [],
}


class LeadCapturePlugin:
    name = "lead_capture"
    description = "Kundenkontakte speichern (Lead-Erfassung für Vertrieb und CRM)"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name des Kunden/Interessenten.",
            },
            "email": {
                "type": "string",
                "description": "E-Mail-Adresse des Kunden.",
            },
            "phone": {
                "type": "string",
                "description": "Telefonnummer des Kunden.",
            },
            "message": {
                "type": "string",
                "description": "Nachricht oder Anfrage des Kunden.",
            },
            "source": {
                "type": "string",
                "enum": ["chat", "website", "email", "phone", "referral", "event", "social", "other"],
                "default": "chat",
                "description": "Quelle des Leads.",
            },
            "status": {
                "type": "string",
                "enum": ["new", "contacted", "qualified", "lost", "converted"],
                "default": "new",
                "description": "Status des Leads.",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags für Kategorisierung (z.B. 'granit', 'marmor', 'küche').",
            },
            "notes": {
                "type": "string",
                "description": "Zusätzliche Notizen zum Lead.",
            },
            "address": {
                "type": "string",
                "description": "Adresse des Kunden (optional).",
            },
            "company": {
                "type": "string",
                "description": "Firmenname (optional).",
            },
            "project": {
                "type": "string",
                "description": "Projektbeschreibung (optional).",
            },
            "interest": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Interessen des Kunden (z.B. ['granit', 'küchenarbeitsplatte']).",
            },
        },
        "required": ["name"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "lead_id": {"type": "string"},
            "lead": {"type": "object"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.storage_path = os.getenv("LEAD_STORAGE_PATH", "./leads.json")
        self._ensure_storage()

    def _ensure_storage(self):
        """Stellt sicher, dass die Speicherdatei existiert."""
        if not os.path.exists(self.storage_path):
            try:
                os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                with open(self.storage_path, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def _load_leads(self) -> list[dict[str, Any]]:
        """Lädt alle Leads aus der JSON-Datei."""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_leads(self, leads: list[dict[str, Any]]):
        """Speichert Leads in der JSON-Datei."""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(leads, f, ensure_ascii=False, indent=2, default=str)
        except Exception:
            pass

    def _generate_id(self) -> str:
        """Generiert eine einfache Lead-ID."""
        import uuid
        return str(uuid.uuid4())[:8]

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        name = str(input_data.get("name", "")).strip()
        if not name:
            return {"success": False, "error": "Name ist erforderlich."}

        email = str(input_data.get("email", "")).strip() or None
        phone = str(input_data.get("phone", "")).strip() or None
        message = str(input_data.get("message", "")).strip() or None
        source = str(input_data.get("source", "chat")).strip()
        status = str(input_data.get("status", "new")).strip()
        tags = input_data.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        notes = str(input_data.get("notes", "")).strip() or None
        address = str(input_data.get("address", "")).strip() or None
        company = str(input_data.get("company", "")).strip() or None
        project = str(input_data.get("project", "")).strip() or None
        interest = input_data.get("interest", [])
        if not isinstance(interest, list):
            interest = []

        # E-Mail-Validierung (einfach)
        if email and "@" not in email:
            return {"success": False, "error": "Ungültige E-Mail-Adresse."}

        # Lead-Objekt erstellen
        lead = {
            "id": self._generate_id(),
            "name": name,
            "email": email,
            "phone": phone,
            "message": message,
            "source": source,
            "status": status,
            "tags": tags,
            "notes": notes,
            "address": address,
            "company": company,
            "project": project,
            "interest": interest,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # In lokaler JSON-Datei speichern
        leads = self._load_leads()
        leads.append(lead)
        self._save_leads(leads)

        # Optional: HubSpot-Integration (falls konfiguriert)
        hubspot_result = await self._send_to_hubspot(lead) if os.getenv("HUBSPOT_API_KEY") else None

        response = {
            "success": True,
            "lead_id": lead["id"],
            "lead": lead,
            "message": f"Lead '{name}' wurde erfolgreich erfasst.",
        }

        if hubspot_result:
            response["hubspot"] = hubspot_result

        return response

    async def _send_to_hubspot(self, lead: dict[str, Any]) -> dict[str, Any]:
        """Sendet den Lead an HubSpot (optional)."""
        hubspot_api_key = os.getenv("HUBSPOT_API_KEY")
        if not hubspot_api_key:
            return {"status": "skipped", "message": "HubSpot API-Key nicht konfiguriert."}

        import httpx

        # HubSpot Contact erstellen
        email = lead.get("email")
        if not email:
            return {"status": "skipped", "message": "Keine E-Mail für HubSpot-Kontakt."}

        properties = {
            "firstname": lead.get("name", "").split()[0] if lead.get("name") else "",
            "lastname": " ".join(lead.get("name", "").split()[1:]) if lead.get("name") else "",
            "email": email,
            "phone": lead.get("phone", ""),
            "company": lead.get("company", ""),
        }

        # Nachricht als Notiz hinzufügen (wenn vorhanden)
        if lead.get("message") or lead.get("notes"):
            properties["hs_notes"] = f"{lead.get('message', '')}\n\n{lead.get('notes', '')}".strip()

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://api.hubapi.com/crm/v3/objects/contacts",
                    headers={
                        "Authorization": f"Bearer {hubspot_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"properties": properties},
                )
                response.raise_for_status()
                return {"status": "success", "message": "Lead an HubSpot gesendet."}
        except Exception as e:
            return {"status": "error", "message": f"HubSpot-Fehler: {str(e)}"}


