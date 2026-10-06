from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_query_service
from app.db.models.user import User
from app.schemas.query import CitationRead, QueryRequest, QueryResponse
from app.services.queries import QueryService

router = APIRouter()


@router.post("/{knowledge_base_id}/queries", response_model=QueryResponse)
def ask(
    knowledge_base_id: UUID,
    body: QueryRequest,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[QueryService, Depends(get_query_service)],
) -> QueryResponse:
    result = service.ask(
        organization_id=user.organization_id,
        user_id=user.id,
        knowledge_base_id=knowledge_base_id,
        question=body.question,
        conversation_id=body.conversation_id,
    )
    return QueryResponse(
        conversation_id=result.conversation_id,
        answer=result.answer,
        provider=result.provider,
        retrieval_mode=result.retrieval_mode,
        citations=[
            CitationRead(
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                document_title=item.document_title,
                excerpt=item.excerpt,
                score=item.score,
            )
            for item in result.citations
        ],
    )
