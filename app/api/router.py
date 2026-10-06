from fastapi import APIRouter

from app.api.routes import auth, conversations, documents, knowledge_bases, queries, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    knowledge_bases.router,
    prefix="/knowledge-bases",
    tags=["knowledge-bases"],
)
api_router.include_router(documents.router, prefix="/knowledge-bases", tags=["documents"])
api_router.include_router(queries.router, prefix="/knowledge-bases", tags=["queries"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
