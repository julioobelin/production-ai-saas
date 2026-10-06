"""Import models so metadata is populated for Alembic."""

from app.db.models.chunk import Chunk
from app.db.models.conversation import Conversation
from app.db.models.document import Document
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.message import Message
from app.db.models.organization import Organization
from app.db.models.user import User

__all__ = [
    "Chunk",
    "Conversation",
    "Document",
    "KnowledgeBase",
    "Message",
    "Organization",
    "User",
]
