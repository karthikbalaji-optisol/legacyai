"""Initial schema for LegacyLens AI

Revision ID: 001_initial
Revises:
Create Date: 2026-10-23 12:00:00

"""
import sqlalchemy as sa
from alembic import op

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'repositories',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=True),
        sa.Column('file_count', sa.Integer(), nullable=True),
        sa.Column('total_size_bytes', sa.Integer(), nullable=True),
        sa.Column('storage_path', sa.String(length=1024), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'analyses',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('repository_id', sa.String(length=36), sa.ForeignKey('repositories.id'), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('current_node', sa.String(length=100), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('scan_summary', sa.JSON(), nullable=True),
        sa.Column('validation_score', sa.Float(), nullable=True),
        sa.Column('review_status', sa.String(length=50), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'evidence_records',
        sa.Column('id', sa.String(length=64), nullable=False, primary_key=True),
        sa.Column('analysis_id', sa.String(length=36), sa.ForeignKey('analyses.id'), nullable=False),
        sa.Column('repository_id', sa.String(length=36), nullable=False),
        sa.Column('relative_path', sa.String(length=1024), nullable=False),
        sa.Column('symbol_name', sa.String(length=255), nullable=False),
        sa.Column('start_line', sa.Integer(), nullable=False),
        sa.Column('end_line', sa.Integer(), nullable=False),
        sa.Column('source_excerpt', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('extraction_method', sa.String(length=50), nullable=True),
        sa.Column('validation_status', sa.String(length=50), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'brd_versions',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('analysis_id', sa.String(length=36), sa.ForeignKey('analyses.id'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('brd_document', sa.JSON(), nullable=False),
        sa.Column('review_status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'review_decisions',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('analysis_id', sa.String(length=36), sa.ForeignKey('analyses.id'), nullable=False),
        sa.Column('requirement_id', sa.String(length=64), nullable=True),
        sa.Column('reviewer_name', sa.String(length=255), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'exports',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('analysis_id', sa.String(length=36), nullable=False),
        sa.Column('export_format', sa.String(length=20), nullable=True),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

def downgrade() -> None:
    op.drop_table('exports')
    op.drop_table('review_decisions')
    op.drop_table('brd_versions')
    op.drop_table('evidence_records')
    op.drop_table('analyses')
    op.drop_table('repositories')
