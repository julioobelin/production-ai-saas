import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest
from app.schemas.document import DocumentCreate
from app.schemas.knowledge_base import KnowledgeBaseCreate


def test_whitespace_only_required_text_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            organization_name="  ",
            email="ada@example.com",
            password="correct-horse",
            full_name="Ada Owner",
        )
    with pytest.raises(ValidationError):
        KnowledgeBaseCreate(name=" ")
    with pytest.raises(ValidationError):
        DocumentCreate(title=" ", content="A real note.")


def test_surrounding_whitespace_is_removed_before_length_checks() -> None:
    created = KnowledgeBaseCreate(name="  Finance  ", description="  Internal notes  ")
    assert created.name == "Finance"
    assert created.description == "Internal notes"
