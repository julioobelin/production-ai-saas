from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.db.models.organization import Organization

_SLUG = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    slug = _SLUG.sub("-", value.casefold()).strip("-")[:60]
    return slug or "organization"


class OrganizationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, *, name: str, slug: str) -> Organization:
        organization = Organization(name=name, slug=slug)
        self._session.add(organization)
        self._session.flush()
        return organization

    def allocate_slug(self, name: str) -> str:
        base = slugify(name)
        candidate = base
        suffix = 2
        while self._slug_taken(candidate):
            candidate = f"{base}-{suffix}"
            suffix += 1
            if suffix > 1000:
                raise ConflictError("Could not allocate an organization slug")
        return candidate

    def _slug_taken(self, slug: str) -> bool:
        statement = select(Organization.id).where(Organization.slug == slug)
        return self._session.scalar(statement) is not None
