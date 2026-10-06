"""Request dependencies. Routes stay thin; services own the rules."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.ai.factory import build_chat_provider, build_embedder, build_retriever
from app.ai.protocols import ChatProvider, Embedder
from app.core.config import Settings, get_settings
from app.core.exceptions import ForbiddenError, InvalidTokenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.models.user import User
from app.db.session import get_db
from app.repositories.chunks import ChunkRepository
from app.repositories.conversations import ConversationRepository
from app.repositories.documents import DocumentRepository
from app.repositories.knowledge_bases import KnowledgeBaseRepository
from app.repositories.messages import MessageRepository
from app.repositories.organizations import OrganizationRepository
from app.repositories.users import UserRepository
from app.schemas.common import PageParams
from app.services.auth import OWNER, AuthService
from app.services.conversations import ConversationService
from app.services.documents import DocumentService
from app.services.knowledge_bases import KnowledgeBaseService
from app.services.queries import QueryService
from app.services.users import UserService

_bearer = HTTPBearer(auto_error=False)


def get_page_params(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PageParams:
    return PageParams(limit=limit, offset=offset)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Authentication is required")
    try:
        token = decode_access_token(credentials.credentials, settings.jwt_secret)
    except InvalidTokenError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc
    user = UserRepository(session).get(token.organization_id, token.user_id)
    if user is None:
        raise UnauthorizedError("Invalid or expired token")
    return user


def require_owner(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != OWNER:
        raise ForbiddenError("Only the organization owner can perform this action")
    return user


def get_embedder(settings: Annotated[Settings, Depends(get_settings)]) -> Embedder | None:
    return build_embedder(settings)


def get_chat_provider(settings: Annotated[Settings, Depends(get_settings)]) -> ChatProvider:
    return build_chat_provider(settings)


def get_auth_service(
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(
        OrganizationRepository(session),
        UserRepository(session),
        jwt_secret=settings.jwt_secret,
        jwt_expire_minutes=settings.jwt_expire_minutes,
    )


def get_user_service(session: Annotated[Session, Depends(get_db)]) -> UserService:
    return UserService(UserRepository(session))


def get_knowledge_base_service(
    session: Annotated[Session, Depends(get_db)],
) -> KnowledgeBaseService:
    return KnowledgeBaseService(KnowledgeBaseRepository(session))


def get_document_service(
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    embedder: Annotated[Embedder | None, Depends(get_embedder)],
) -> DocumentService:
    return DocumentService(
        DocumentRepository(session),
        ChunkRepository(session),
        KnowledgeBaseRepository(session),
        embedder=embedder,
        retrieval_mode=settings.retrieval_mode,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        max_document_chars=settings.max_document_chars,
    )


def get_query_service(
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    embedder: Annotated[Embedder | None, Depends(get_embedder)],
    chat: Annotated[ChatProvider, Depends(get_chat_provider)],
) -> QueryService:
    return QueryService(
        KnowledgeBaseRepository(session),
        ConversationRepository(session),
        MessageRepository(session),
        retriever=build_retriever(session, settings, embedder),
        chat=chat,
        retrieval_limit=settings.retrieval_limit,
    )


def get_conversation_service(
    session: Annotated[Session, Depends(get_db)],
) -> ConversationService:
    return ConversationService(ConversationRepository(session), MessageRepository(session))
