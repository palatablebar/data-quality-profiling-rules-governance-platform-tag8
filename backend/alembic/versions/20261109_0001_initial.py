"""initial schema

Revision ID: 20261109_0001
Revises:
Create Date: 2026-11-09

The runtime app bootstraps with ``Base.metadata.create_all`` (see README);
this migration exists so the project can also be deployed with
``alembic upgrade head`` on a fresh MySQL instance.
"""
from alembic import op

from app.config.database import Base
import app.models  # noqa: F401

revision = "20261109_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
