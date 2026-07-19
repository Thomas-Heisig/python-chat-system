"""plugin_governance_tables

Revision ID: 6f9c2e7a4d31
Revises: dbc518d8de8c
Create Date: 2026-07-18 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6f9c2e7a4d31"
down_revision: Union[str, Sequence[str], None] = "dbc518d8de8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "plugin_confirmations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("confirmation_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("plugin_id", sa.String(length=120), nullable=False),
        sa.Column("function_name", sa.String(length=120), nullable=False),
        sa.Column("route_kind", sa.String(length=40), nullable=False),
        sa.Column("arguments_json", sa.JSON(), nullable=False),
        sa.Column("arguments_hash", sa.String(length=64), nullable=False),
        sa.Column("plugin_settings_json", sa.JSON(), nullable=False),
        sa.Column("execution_context_json", sa.JSON(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("confirmation_id"),
    )
    op.create_index(op.f("ix_plugin_confirmations_confirmation_id"), "plugin_confirmations", ["confirmation_id"], unique=False)
    op.create_index(op.f("ix_plugin_confirmations_expires_at"), "plugin_confirmations", ["expires_at"], unique=False)
    op.create_index(op.f("ix_plugin_confirmations_function_name"), "plugin_confirmations", ["function_name"], unique=False)
    op.create_index(op.f("ix_plugin_confirmations_plugin_id"), "plugin_confirmations", ["plugin_id"], unique=False)
    op.create_index(op.f("ix_plugin_confirmations_status"), "plugin_confirmations", ["status"], unique=False)
    op.create_index(op.f("ix_plugin_confirmations_team_id"), "plugin_confirmations", ["team_id"], unique=False)
    op.create_index(op.f("ix_plugin_confirmations_user_id"), "plugin_confirmations", ["user_id"], unique=False)

    op.create_table(
        "plugin_idempotency_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plugin_id", sa.String(length=120), nullable=False),
        sa.Column("function_name", sa.String(length=120), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("user_scope", sa.String(length=80), nullable=False),
        sa.Column("team_scope", sa.String(length=80), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("arguments_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("response_json", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("last_executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "plugin_id",
            "function_name",
            "user_scope",
            "team_scope",
            "idempotency_key",
            name="uq_plugin_idempotency_scope",
        ),
    )
    op.create_index(op.f("ix_plugin_idempotency_records_function_name"), "plugin_idempotency_records", ["function_name"], unique=False)
    op.create_index(op.f("ix_plugin_idempotency_records_lease_expires_at"), "plugin_idempotency_records", ["lease_expires_at"], unique=False)
    op.create_index(op.f("ix_plugin_idempotency_records_plugin_id"), "plugin_idempotency_records", ["plugin_id"], unique=False)
    op.create_index(op.f("ix_plugin_idempotency_records_status"), "plugin_idempotency_records", ["status"], unique=False)
    op.create_index(op.f("ix_plugin_idempotency_records_team_id"), "plugin_idempotency_records", ["team_id"], unique=False)
    op.create_index(op.f("ix_plugin_idempotency_records_team_scope"), "plugin_idempotency_records", ["team_scope"], unique=False)
    op.create_index(op.f("ix_plugin_idempotency_records_user_id"), "plugin_idempotency_records", ["user_id"], unique=False)
    op.create_index(op.f("ix_plugin_idempotency_records_user_scope"), "plugin_idempotency_records", ["user_scope"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_plugin_idempotency_records_user_scope"), table_name="plugin_idempotency_records")
    op.drop_index(op.f("ix_plugin_idempotency_records_user_id"), table_name="plugin_idempotency_records")
    op.drop_index(op.f("ix_plugin_idempotency_records_team_scope"), table_name="plugin_idempotency_records")
    op.drop_index(op.f("ix_plugin_idempotency_records_team_id"), table_name="plugin_idempotency_records")
    op.drop_index(op.f("ix_plugin_idempotency_records_status"), table_name="plugin_idempotency_records")
    op.drop_index(op.f("ix_plugin_idempotency_records_plugin_id"), table_name="plugin_idempotency_records")
    op.drop_index(op.f("ix_plugin_idempotency_records_lease_expires_at"), table_name="plugin_idempotency_records")
    op.drop_index(op.f("ix_plugin_idempotency_records_function_name"), table_name="plugin_idempotency_records")
    op.drop_table("plugin_idempotency_records")

    op.drop_index(op.f("ix_plugin_confirmations_user_id"), table_name="plugin_confirmations")
    op.drop_index(op.f("ix_plugin_confirmations_team_id"), table_name="plugin_confirmations")
    op.drop_index(op.f("ix_plugin_confirmations_status"), table_name="plugin_confirmations")
    op.drop_index(op.f("ix_plugin_confirmations_plugin_id"), table_name="plugin_confirmations")
    op.drop_index(op.f("ix_plugin_confirmations_function_name"), table_name="plugin_confirmations")
    op.drop_index(op.f("ix_plugin_confirmations_expires_at"), table_name="plugin_confirmations")
    op.drop_index(op.f("ix_plugin_confirmations_confirmation_id"), table_name="plugin_confirmations")
    op.drop_table("plugin_confirmations")
