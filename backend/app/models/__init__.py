"""All SQLModel table models are imported here so Alembic sees them on autogenerate."""

from app.models.user import User

__all__ = ["User"]
