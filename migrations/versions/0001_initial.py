"""Initial document, extraction, and review tables."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False, unique=True),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "processing",
                "completed",
                "review_required",
                "failed",
                name="documentstatus",
            ),
            nullable=False,
        ),
        sa.Column("schema_name", sa.String(80), nullable=False),
        sa.Column("error_code", sa.String(80)),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_sha256", "documents", ["sha256"])
    op.create_table(
        "extractions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "document_id", sa.String(36), sa.ForeignKey("documents.id"), nullable=False, unique=True
        ),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("text_method", sa.String(40), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("validation_errors", sa.JSON(), nullable=False),
        sa.Column("field_confidence", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "document_id", sa.String(36), sa.ForeignKey("documents.id"), nullable=False, unique=True
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "corrected", name="reviewstatus"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("corrected_data", sa.JSON()),
        sa.Column("reviewer", sa.String(120)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
    )


def downgrade():
    op.drop_table("reviews")
    op.drop_table("extractions")
    op.drop_index("ix_documents_sha256", table_name="documents")
    op.drop_table("documents")
