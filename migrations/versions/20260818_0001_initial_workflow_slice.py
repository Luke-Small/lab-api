"""Initial workflow vertical slice.

Revision ID: 20260818_0001
Revises:
Create Date: 2026-08-18
"""
from alembic import op
import sqlalchemy as sa

revision = "20260818_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "experiments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "samples",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("barcode", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("barcode"),
    )
    op.create_index("ix_samples_experiment_id", "samples", ["experiment_id"])
    op.create_table(
        "print_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("sample_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.Enum("queued", "running", "completed", "failed", name="printjobstatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"]),
        sa.ForeignKeyConstraint(["sample_id"], ["samples.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_print_jobs_experiment_id", "print_jobs", ["experiment_id"])
    op.create_index("ix_print_jobs_sample_id", "print_jobs", ["sample_id"])
    op.create_table(
        "printer_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("print_job_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.Enum("started", "completed", "failed", name="printereventtype"), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["print_job_id"], ["print_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("print_job_id", "idempotency_key", name="uq_printer_event_idempotency"),
    )
    op.create_index("ix_printer_events_print_job_id", "printer_events", ["print_job_id"])
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("print_job_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["print_job_id"], ["print_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "form_submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("experiment_id", sa.Uuid(), nullable=False),
        sa.Column("sample_id", sa.Uuid(), nullable=False),
        sa.Column("form_type", sa.String(length=100), nullable=False),
        sa.Column("values", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"]),
        sa.ForeignKeyConstraint(["sample_id"], ["samples.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_form_submissions_experiment_id", "form_submissions", ["experiment_id"])
    op.create_index("ix_form_submissions_sample_id", "form_submissions", ["sample_id"])


def downgrade() -> None:
    op.drop_table("form_submissions")
    op.drop_table("notifications")
    op.drop_table("printer_events")
    op.drop_table("print_jobs")
    op.drop_table("samples")
    op.drop_table("experiments")
