from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.error_handlers import register_error_handlers
from app.api.routes import (
    auth_router,
    chat_router,
    conversations_router,
    health_router,
    messages_router,
    meta_router,
    models_router,
    settings_router,
    system_router,
    workspace_router,
)
from app.training.api import training_router
from app.lifespan import app_lifespan
from app.core.config import get_config


app = FastAPI(title="Python Chat System", lifespan=app_lifespan)
register_error_handlers(app)

config = get_config()
allowed_origins = [origin.strip() for origin in config.cors_allow_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=config.cors_allow_origin_regex,
    allow_credentials=config.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(models_router)
app.include_router(settings_router)
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(messages_router)
app.include_router(workspace_router)
app.include_router(training_router)
app.include_router(meta_router)
app.include_router(system_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "python-chat-system", "status": "running"}
