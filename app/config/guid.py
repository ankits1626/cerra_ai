import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator


class GUID(TypeDecorator):
    """
    Platform-independent GUID/UUID type for SQLAlchemy.

    This custom type allows for seamless handling of UUID fields across different database engines.

    - For databases that natively support UUID (like PostgreSQL), it uses the UUID type.
    - For databases that do not support UUID (like SQLite), it stores the UUID as a string.

    Usage:
        Use `GUID()` in your SQLAlchemy model definitions to define a UUID field:

        id = Column(GUID(), primary_key=True, default=uuid.uuid4, nullable=False)

    Methods:
        load_dialect_impl(dialect): Determines which type to use based on the database dialect.
        process_bind_param(value, dialect): Converts the UUID to a string when storing in SQLite.
        process_result_value(value, dialect): Converts the stored string back to a UUID when retrieving from SQLite.
    """

    impl = sa.String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """
        Determine which type to use for the UUID based on the database dialect.

        Args:
            dialect: The database dialect (e.g., 'postgresql', 'sqlite').

        Returns:
            The appropriate type descriptor for the given dialect.
        """
        if dialect.name == "sqlite":
            return dialect.type_descriptor(sa.String(36))  # Use string for SQLite
        else:
            return dialect.type_descriptor(
                UUID(as_uuid=True)
            )  # Use UUID for PostgreSQL

    def process_bind_param(self, value, dialect):
        """
        Process the value before it is sent to the database.

        For SQLite, this method converts UUIDs to strings. PostgreSQL handles UUIDs natively,
        so no conversion is necessary.

        Args:
            value: The value to be stored in the database (UUID or None).
            dialect: The database dialect (e.g., 'postgresql', 'sqlite').

        Returns:
            A string if storing in SQLite, otherwise the original UUID object.
        """
        if value is None:
            return None
        if dialect.name == "sqlite":  # For SQLite, convert UUID to string
            if isinstance(value, uuid.UUID):
                return str(value)  # Ensure UUID is stored as a string
            return value
        else:
            if isinstance(value, uuid.UUID):
                return value  # PostgreSQL handles UUID natively
            return str(value)

    def process_result_value(self, value, dialect):
        """
        Process the value after it is retrieved from the database.

        This method converts strings back to UUIDs for SQLite. PostgreSQL can return UUIDs directly.

        Args:
            value: The value retrieved from the database (string or UUID).
            dialect: The database dialect (e.g., 'postgresql', 'sqlite').

        Returns:
            A UUID object if using SQLite, otherwise the original value.
        """
        if value is None:
            return None
        if dialect.name == "sqlite":
            return uuid.UUID(value)  # Convert string back to UUID in SQLite
        else:
            return value
