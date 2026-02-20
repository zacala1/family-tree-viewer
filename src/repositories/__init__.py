"""Repository layer for data access abstraction."""

from .person_repository import PersonRepository
from .relationship_repository import RelationshipRepository

__all__ = ["PersonRepository", "RelationshipRepository"]
