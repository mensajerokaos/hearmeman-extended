"""
Repository Module

Factory and registry for all repository classes.
"""

from typing import Type, Dict, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.base import Base
from api.repositories.base import BaseRepository
from api.repositories.job import JobRepository
from api.repositories.media import MediaRepository
from api.repositories.result import ResultRepository
from api.repositories.transcription import TranscriptionRepository
from api.repositories.processing_log import ProcessingLogRepository


# Type variable for models
M = TypeVar("M", bound=Base)


class RepositoryFactory:
    """
    Factory for creating repository instances.

    Provides a centralized way to create and manage repository instances
    with proper type hints and dependency injection support.
    """

    _registry: Dict[str, Type[BaseRepository]] = {}

    @classmethod
    def register(cls, name: str) -> callable:
        """
        Decorator to register a repository class.

        Args:
            name: Repository name (usually model name in snake_case)

        Returns:
            Decorator function
        """
        def decorator(repository_class: Type[BaseRepository]) -> Type[BaseRepository]:
            cls._registry[name] = repository_class
            return repository_class
        return decorator

    @classmethod
    def create(
        cls,
        session: AsyncSession,
        model: Type[Base]
    ) -> BaseRepository:
        """
        Create a repository instance for a given model.

        Args:
            session: AsyncSession instance
            model: SQLAlchemy model class

        Returns:
            Repository instance for the model
        """
        model_name = model.__name__.lower()

        if model_name in cls._registry:
            repository_class = cls._registry[model_name]
            return repository_class(session)

        # Fallback to generic BaseRepository
        return BaseRepository(model, session)

    @classmethod
    def get_registry(cls) -> Dict[str, Type[BaseRepository]]:
        """
        Get all registered repositories.

        Returns:
            Dictionary of registered repositories
        """
        return cls._registry.copy()


# Convenience function for creating repositories
def get_repository(session: AsyncSession, model: Type[Base]) -> BaseRepository:
    """
    Get a repository instance for the given model.

    Args:
        session: AsyncSession instance
        model: SQLAlchemy model class

    Returns:
        Repository instance
    """
    return RepositoryFactory.create(session, model)


# Auto-register built-in repositories
RepositoryFactory.register("job")(JobRepository)
RepositoryFactory.register("media")(MediaRepository)
RepositoryFactory.register("result")(ResultRepository)
RepositoryFactory.register("transcription")(TranscriptionRepository)
RepositoryFactory.register("processing_log")(ProcessingLogRepository)


__all__ = [
    "BaseRepository",
    "JobRepository",
    "MediaRepository",
    "ResultRepository",
    "TranscriptionRepository",
    "ProcessingLogRepository",
    "RepositoryFactory",
    "get_repository",
]
