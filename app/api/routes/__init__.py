from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.models import router as models_router
from app.api.routes.settings import router as settings_router
from app.api.routes.chat import router as chat_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.messages import router as messages_router
from app.api.routes.workspace import router as workspace_router
from app.api.routes.meta import router as meta_router
from app.api.routes.system import router as system_router
from app.api.routes.speech import router as speech_router
from app.api.routes.plugins import router as plugins_router

__all__ = [
	"health_router",
	"auth_router",
	"models_router",
	"settings_router",
	"chat_router",
	"conversations_router",
	"messages_router",
	"workspace_router",
	"meta_router",
	"system_router",
	"speech_router",
	"plugins_router",
]
