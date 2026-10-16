from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Predictable names for indexes/constraints so Alembic migrations stay consistent
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Parent class for every model; collects all tables into Base.metadata."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
