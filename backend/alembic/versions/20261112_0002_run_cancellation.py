"""run cancellation: cancelled status bookkeeping columns

Revision ID: 20261112_0002
Revises: 20261109_0001
Create Date: 2026-11-12

Adds the columns that make aborting a batch a first-class, race-free outcome:

* ``rule_runs.rule_ids`` — snapshot of the batch's rules (drives cancel bookkeeping)
* ``rule_runs.lock_token`` — proves which batch holds the dataset lock
* ``rule_runs.rules_unfinished`` — how many rules never finished
* ``rule_run_items.status`` — finished | cancelled placeholder per rule

The runtime bootstrap applies the same columns idempotently
(``app.config.database._ensure_runtime_columns``); this migration is for
deployments managed with ``alembic upgrade head``.
"""
from alembic import op

revision = "20261112_0002"
down_revision = "20261109_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE rule_runs ADD COLUMN rule_ids JSON NULL")
    op.execute("ALTER TABLE rule_runs ADD COLUMN lock_token VARCHAR(64) NULL")
    op.execute("ALTER TABLE rule_runs ADD COLUMN rules_unfinished INT NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE rule_run_items ADD COLUMN status VARCHAR(16) NOT NULL DEFAULT 'finished'")


def downgrade() -> None:
    op.execute("ALTER TABLE rule_run_items DROP COLUMN status")
    op.execute("ALTER TABLE rule_runs DROP COLUMN rules_unfinished")
    op.execute("ALTER TABLE rule_runs DROP COLUMN lock_token")
    op.execute("ALTER TABLE rule_runs DROP COLUMN rule_ids")
