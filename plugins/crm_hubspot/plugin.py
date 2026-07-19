# packages/plugins/crm_hubspot/plugin.py
from __future__ import annotations

import json
import os
from typing import Any, cast

import httpx


PLUGIN_META: dict[str, Any] = {
    "id": "crm_hubspot",
    "name": "HubSpot CRM",
    "description": "HubSpot CRM-Integration für Kontakt-, Unternehmens- und Deal-Management",
    "category": "📊 Business & Analytics",
    "apiKeyRequired": True,
    "intentPattern": r"\b(kunde|kontakt|adresse|telefon|email|crm|hubspot|deal|unternehmen)\b",
    "status": "implemented",
    "settingsFields": [],
}


class HubSpotCRMPlugin:
    name = "crm_hubspot"
    description = "HubSpot CRM-Integration für Kontakt-, Unternehmens- und Deal-Management"

    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "list_contacts",
                    "get_contact",
                    "create_contact",
                    "update_contact",
                    "search_contacts",
                    "list_deals",
                    "create_deal",
                    "list_tasks",
                    "create_task",
                ],
                "default": "list_contacts",
                "description": "Aktion im HubSpot CRM.",
            },
            "contact_id": {
                "type": "string",
                "description": "HubSpot Kontakt-ID (für get_contact, update_contact).",
            },
            "email": {
                "type": "string",
                "description": "E-Mail-Adresse (für search_contacts, create_contact).",
            },
            "firstname": {"type": "string", "description": "Vorname (für create_contact)."},
            "lastname": {"type": "string", "description": "Nachname (für create_contact)."},
            "phone": {"type": "string", "description": "Telefonnummer (für create_contact)."},
            "company": {"type": "string", "description": "Firmenname (für create_contact)."},
            "deal_name": {"type": "string", "description": "Deal-Name (für create_deal)."},
            "deal_amount": {"type": "number", "description": "Deal-Betrag (für create_deal)."},
            "deal_stage": {
                "type": "string",
                "enum": ["appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "decisionmakerbought", "contractsent", "closedwon", "closedlost"],
                "default": "appointmentscheduled",
                "description": "Deal-Phase (für create_deal).",
            },
            "task_title": {"type": "string", "description": "Aufgabentitel (für create_task)."},
            "task_description": {"type": "string", "description": "Aufgabenbeschreibung (für create_task)."},
            "task_due_date": {"type": "string", "description": "Fälligkeitsdatum YYYY-MM-DD (für create_task)."},
            "limit": {"type": "integer", "default": 10, "description": "Max. Anzahl Ergebnisse (für Listen)."},
            "query": {"type": "string", "description": "Suchbegriff (für search_contacts)."},
        },
        "required": ["action"],
    }

    output_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "data": {"type": "array"},
            "total": {"type": "integer"},
            "contact": {"type": "object"},
            "error": {"type": "string"},
        },
    }

    def __init__(self):
        self.api_key = os.getenv("HUBSPOT_API_KEY", "")
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _is_configured(self) -> bool:
        return bool(self.api_key)

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Führt einen HTTP-Request an die HubSpot API durch."""
        if not self._is_configured():
            return {"error": "HubSpot API-Key nicht konfiguriert. Setze HUBSPOT_API_KEY in der Umgebung."}

        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params,
                )
                response.raise_for_status()
                return cast(dict[str, Any], response.json())
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    return {"error": "Rate-Limit überschritten. Bitte später erneut versuchen."}
                if e.response.status_code == 401:
                    return {"error": "Ungültiger API-Key. Prüfe HUBSPOT_API_KEY."}
                if e.response.status_code == 404:
                    return {"error": "Ressource nicht gefunden."}
                return {"error": f"HTTP-Fehler: {e.response.status_code}"}
            except Exception as e:
                return {"error": f"Fehler: {str(e)}"}

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        action = str(input_data.get("action", "list_contacts")).lower()

        if not self._is_configured():
            return {
                "success": False,
                "error": "HubSpot API-Key nicht konfiguriert. Setze HUBSPOT_API_KEY in der Umgebung.",
            }

        if action == "list_contacts":
            return await self._list_contacts(input_data)
        elif action == "get_contact":
            return await self._get_contact(input_data)
        elif action == "create_contact":
            return await self._create_contact(input_data)
        elif action == "update_contact":
            return await self._update_contact(input_data)
        elif action == "search_contacts":
            return await self._search_contacts(input_data)
        elif action == "list_deals":
            return await self._list_deals(input_data)
        elif action == "create_deal":
            return await self._create_deal(input_data)
        elif action == "list_tasks":
            return await self._list_tasks(input_data)
        elif action == "create_task":
            return await self._create_task(input_data)
        else:
            return {"success": False, "error": f"Unbekannte Aktion: {action}"}

    async def _list_contacts(self, input_data: dict[str, Any]) -> dict[str, Any]:
        limit = max(1, min(100, int(input_data.get("limit", 10))))
        result = await self._request(
            "GET",
            "/crm/v3/objects/contacts",
            params={"limit": limit, "properties": "firstname,lastname,email,phone,company"},
        )
        if "error" in result:
            return {"success": False, "error": result["error"]}
        results = result.get("results", [])
        return {
            "success": True,
            "data": results,
            "total": result.get("total", len(results)),
            "message": f"{len(results)} Kontakte gefunden.",
        }

    async def _get_contact(self, input_data: dict[str, Any]) -> dict[str, Any]:
        contact_id = str(input_data.get("contact_id", "")).strip()
        if not contact_id:
            return {"success": False, "error": "contact_id ist erforderlich."}
        result = await self._request(
            "GET",
            f"/crm/v3/objects/contacts/{contact_id}",
            params={"properties": "firstname,lastname,email,phone,company"},
        )
        if "error" in result:
            return {"success": False, "error": result["error"]}
        return {"success": True, "contact": result, "message": "Kontakt gefunden."}

    async def _create_contact(self, input_data: dict[str, Any]) -> dict[str, Any]:
        properties: dict[str, Any] = {}
        if input_data.get("firstname"):
            properties["firstname"] = str(input_data["firstname"])
        if input_data.get("lastname"):
            properties["lastname"] = str(input_data["lastname"])
        if input_data.get("email"):
            properties["email"] = str(input_data["email"])
        if input_data.get("phone"):
            properties["phone"] = str(input_data["phone"])
        if input_data.get("company"):
            properties["company"] = str(input_data["company"])

        if not properties:
            return {"success": False, "error": "Mindestens ein Feld (firstname, email) ist erforderlich."}

        result = await self._request("POST", "/crm/v3/objects/contacts", data={"properties": properties})
        if "error" in result:
            return {"success": False, "error": result["error"]}
        return {"success": True, "contact": result, "message": "Kontakt erstellt."}

    async def _update_contact(self, input_data: dict[str, Any]) -> dict[str, Any]:
        contact_id = str(input_data.get("contact_id", "")).strip()
        if not contact_id:
            return {"success": False, "error": "contact_id ist erforderlich."}
        properties: dict[str, Any] = {}
        if input_data.get("firstname"):
            properties["firstname"] = str(input_data["firstname"])
        if input_data.get("lastname"):
            properties["lastname"] = str(input_data["lastname"])
        if input_data.get("email"):
            properties["email"] = str(input_data["email"])
        if input_data.get("phone"):
            properties["phone"] = str(input_data["phone"])
        if input_data.get("company"):
            properties["company"] = str(input_data["company"])
        if not properties:
            return {"success": False, "error": "Mindestens ein Feld zum Aktualisieren erforderlich."}
        result = await self._request(
            "PATCH",
            f"/crm/v3/objects/contacts/{contact_id}",
            data={"properties": properties},
        )
        if "error" in result:
            return {"success": False, "error": result["error"]}
        return {"success": True, "contact": result, "message": "Kontakt aktualisiert."}

    async def _search_contacts(self, input_data: dict[str, Any]) -> dict[str, Any]:
        query = str(input_data.get("query", "")).strip()
        email = str(input_data.get("email", "")).strip()
        if not query and not email:
            return {"success": False, "error": "query oder email ist erforderlich."}
        limit = max(1, min(100, int(input_data.get("limit", 10))))

        if email:
            # Suche nach E-Mail
            filter_group = {
                "filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}]
            }
            result = await self._request(
                "POST",
                "/crm/v3/objects/contacts/search",
                data={"limit": limit, "filterGroups": filter_group["filterGroups"]},
            )
        else:
            # Suche nach Name
            result = await self._request(
                "POST",
                "/crm/v3/objects/contacts/search",
                data={"limit": limit, "query": query},
            )
        if "error" in result:
            return {"success": False, "error": result["error"]}
        results = result.get("results", [])
        return {"success": True, "data": results, "total": len(results)}

    async def _list_deals(self, input_data: dict[str, Any]) -> dict[str, Any]:
        limit = max(1, min(100, int(input_data.get("limit", 10))))
        result = await self._request(
            "GET",
            "/crm/v3/objects/deals",
            params={"limit": limit, "properties": "dealname,amount,dealstage,closedate"},
        )
        if "error" in result:
            return {"success": False, "error": result["error"]}
        results = result.get("results", [])
        return {
            "success": True,
            "data": results,
            "total": result.get("total", len(results)),
            "message": f"{len(results)} Deals gefunden.",
        }

    async def _create_deal(self, input_data: dict[str, Any]) -> dict[str, Any]:
        deal_name = str(input_data.get("deal_name", "")).strip()
        if not deal_name:
            return {"success": False, "error": "deal_name ist erforderlich."}
        amount = input_data.get("deal_amount", 0)
        deal_stage = str(input_data.get("deal_stage", "appointmentscheduled"))
        properties = {
            "dealname": deal_name,
            "amount": amount,
            "dealstage": deal_stage,
        }
        result = await self._request("POST", "/crm/v3/objects/deals", data={"properties": properties})
        if "error" in result:
            return {"success": False, "error": result["error"]}
        return {"success": True, "deal": result, "message": "Deal erstellt."}

    async def _list_tasks(self, input_data: dict[str, Any]) -> dict[str, Any]:
        limit = max(1, min(100, int(input_data.get("limit", 10))))
        result = await self._request(
            "GET",
            "/crm/v3/objects/tasks",
            params={"limit": limit, "properties": "hs_task_body,hs_task_subject,hs_task_status,hs_task_due_date"},
        )
        if "error" in result:
            return {"success": False, "error": result["error"]}
        results = result.get("results", [])
        return {
            "success": True,
            "data": results,
            "total": result.get("total", len(results)),
            "message": f"{len(results)} Aufgaben gefunden.",
        }

    async def _create_task(self, input_data: dict[str, Any]) -> dict[str, Any]:
        title = str(input_data.get("task_title", "")).strip()
        if not title:
            return {"success": False, "error": "task_title ist erforderlich."}
        description = str(input_data.get("task_description", "")).strip()
        due_date = str(input_data.get("task_due_date", "")).strip()
        properties = {
            "hs_task_subject": title,
            "hs_task_body": description,
            "hs_task_status": "NOT_STARTED",
        }
        if due_date:
            properties["hs_task_due_date"] = due_date
        result = await self._request("POST", "/crm/v3/objects/tasks", data={"properties": properties})
        if "error" in result:
            return {"success": False, "error": result["error"]}
        return {"success": True, "task": result, "message": "Aufgabe erstellt."}

