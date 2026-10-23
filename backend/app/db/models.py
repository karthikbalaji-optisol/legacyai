import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.app.db.database import Base


class RepositoryModel(Base):
    __tablename__ = "repositories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    source_type = Column(String(50), default="zip_upload")
    file_count = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    storage_path = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    analyses = relationship("AnalysisModel", back_populates="repository", cascade="all, delete-orphan")

class AnalysisModel(Base):
    __tablename__ = "analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, scanning, analyzing, completed, failed
    current_node = Column(String(100), default="validate_repository")
    progress_percentage = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    scan_summary = Column(JSON, nullable=True)
    validation_score = Column(Float, default=0.0)
    review_status = Column(String(50), default="PENDING")
    started_at = Column(DateTime, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)

    repository = relationship("RepositoryModel", back_populates="analyses")
    evidence_records = relationship("EvidenceModel", back_populates="analysis", cascade="all, delete-orphan")
    brd_versions = relationship("BRDVersionModel", back_populates="analysis", cascade="all, delete-orphan")
    review_decisions = relationship("ReviewDecisionModel", back_populates="analysis", cascade="all, delete-orphan")

class EvidenceModel(Base):
    __tablename__ = "evidence_records"

    id = Column(String(64), primary_key=True)
    analysis_id = Column(String(36), ForeignKey("analyses.id"), nullable=False)
    repository_id = Column(String(36), nullable=False)
    relative_path = Column(String(1024), nullable=False)
    symbol_name = Column(String(255), nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    source_excerpt = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    extraction_method = Column(String(50), default="ast_scanner")
    validation_status = Column(String(50), default="valid")
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    analysis = relationship("AnalysisModel", back_populates="evidence_records")

class BRDVersionModel(Base):
    __tablename__ = "brd_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), ForeignKey("analyses.id"), nullable=False)
    version = Column(Integer, default=1)
    brd_document = Column(JSON, nullable=False)
    review_status = Column(String(50), default="PENDING")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    analysis = relationship("AnalysisModel", back_populates="brd_versions")

class ReviewDecisionModel(Base):
    __tablename__ = "review_decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), ForeignKey("analyses.id"), nullable=False)
    requirement_id = Column(String(64), nullable=True)  # Null if overall BRD review
    reviewer_name = Column(String(255), nullable=False)
    decision = Column(String(50), nullable=False)  # APPROVED, REJECTED, NEEDS_REVISION
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    analysis = relationship("AnalysisModel", back_populates="review_decisions")

class ExportModel(Base):
    __tablename__ = "exports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), nullable=False)
    export_format = Column(String(20), default="docx")
    file_path = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
