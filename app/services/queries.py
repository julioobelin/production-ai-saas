from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.ai.protocols import ChatProvider, Retriever
from app.ai.types import ChatTurn, Citation, RetrievedPassage
from app.core.exceptions import NotFoundError, ProviderError
from app.repositories.conversations import ConversationRepository
from app.repositories.knowledge_bases import KnowledgeBaseRepository
from app.repositories.messages import MessageRepository

logger = logging.getLogger("app.query")
HISTORY_LIMIT = 6


@dataclass(frozen=True)
class QueryResult:
    conversation_id: uuid.UUID
    answer: str
    provider: str
    retrieval_mode: str
    citations: list[Citation]


class QueryService:
    def __init__(
        self,
        knowledge_bases: KnowledgeBaseRepository,
        conversations: ConversationRepository,
        messages: MessageRepository,
        *,
        retriever: Retriever,
        chat: ChatProvider,
        retrieval_limit: int,
    ) -> None:
        self._knowledge_bases = knowledge_bases
        self._conversations = conversations
        self._messages = messages
        self._retriever = retriever
        self._chat = chat
        self._retrieval_limit = retrieval_limit

    def ask(
        self,
        *,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        question: str,
        conversation_id: uuid.UUID | None,
    ) -> QueryResult:
        if self._knowledge_bases.get(organization_id, knowledge_base_id) is None:
            raise NotFoundError("Knowledge base not found")
        conversation = self._conversation(
            organization_id=organization_id,
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            question=question,
            conversation_id=conversation_id,
        )
        prior = self._messages.latest(
            organization_id,
            conversation.id,
            limit=HISTORY_LIMIT,
        )
        history = [
            ChatTurn(role=message.role, content=message.content) for message in reversed(prior)
        ]
        # The retriever was chosen when the process was wired. Do not switch modes here.
        citations = self._retriever.search(
            organization_id=organization_id,
            knowledge_base_id=knowledge_base_id,
            query=question,
            limit=self._retrieval_limit,
        )
        answer = self._chat.complete(
            question=question,
            history=history,
            passages=[
                RetrievedPassage(document_title=item.document_title, content=item.excerpt)
                for item in citations
            ],
        )
        if not answer.strip():
            raise ProviderError("The language model returned an empty answer")
        created = datetime.now(UTC)
        self._messages.add(
            organization_id=organization_id,
            conversation_id=conversation.id,
            role="user",
            content=question,
            created_at=created,
        )
        self._messages.add(
            organization_id=organization_id,
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            citations=[_citation_payload(item) for item in citations],
            provider_name=self._chat.name,
            retrieval_mode=self._retriever.mode,
            created_at=created + timedelta(microseconds=1),
        )
        logger.info(
            "query_answered",
            extra={
                "event": "query_answered",
                "retrieval_mode": self._retriever.mode,
                "provider": self._chat.name,
                "citation_count": len(citations),
            },
        )
        return QueryResult(
            conversation_id=conversation.id,
            answer=answer,
            provider=self._chat.name,
            retrieval_mode=self._retriever.mode,
            citations=citations,
        )

    def _conversation(
        self,
        *,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        question: str,
        conversation_id: uuid.UUID | None,
    ):
        if conversation_id is None:
            return self._conversations.add(
                organization_id=organization_id,
                knowledge_base_id=knowledge_base_id,
                user_id=user_id,
                title=_title(question),
            )
        conversation = self._conversations.get_for_user(
            organization_id,
            user_id,
            conversation_id,
        )
        if conversation is None or conversation.knowledge_base_id != knowledge_base_id:
            raise NotFoundError("Conversation not found")
        return conversation


def _title(question: str) -> str:
    compact = " ".join(question.split())
    if len(compact) <= 80:
        return compact
    return compact[:77].rstrip() + "..."


def _citation_payload(citation: Citation) -> dict[str, object]:
    return {
        "chunk_id": str(citation.chunk_id),
        "document_id": str(citation.document_id),
        "document_title": citation.document_title,
        "excerpt": citation.excerpt,
        "score": citation.score,
    }
