from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    details: dict[str, str] = {}
