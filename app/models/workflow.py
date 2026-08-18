import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, DateTime, Enum as SqlEnum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PrintJobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class PrinterEventType(str, Enum):
    started = "started"
    completed = "completed"
    failed = "failed"


def uuid_primary_key() -> Mapped[uuid.UUID]:
    return mapped_column(primary_key=True, default=uuid.uuid4)


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Experiment(Timestamped, Base):
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = uuid_primary_key()
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    samples: Mapped[list["Sample"]] = relationship(back_populates="experiment")
    print_jobs: Mapped[list["PrintJob"]] = relationship(back_populates="experiment")


class Sample(Timestamped, Base):
    __tablename__ = "samples"

    id: Mapped[uuid.UUID] = uuid_primary_key()
    experiment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experiments.id"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(200), unique=True, nullable=True)
    experiment: Mapped[Experiment] = relationship(back_populates="samples")
    print_jobs: Mapped[list["PrintJob"]] = relationship(back_populates="sample")


class PrintJob(Timestamped, Base):
    __tablename__ = "print_jobs"

    id: Mapped[uuid.UUID] = uuid_primary_key()
    experiment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experiments.id"), nullable=False, index=True)
    sample_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("samples.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[PrintJobStatus] = mapped_column(SqlEnum(PrintJobStatus), default=PrintJobStatus.queued, nullable=False)
    experiment: Mapped[Experiment] = relationship(back_populates="print_jobs")
    sample: Mapped[Sample] = relationship(back_populates="print_jobs")
    events: Mapped[list["PrinterEvent"]] = relationship(back_populates="print_job")


class PrinterEvent(Timestamped, Base):
    __tablename__ = "printer_events"
    __table_args__ = (UniqueConstraint("print_job_id", "idempotency_key", name="uq_printer_event_idempotency"),)

    id: Mapped[uuid.UUID] = uuid_primary_key()
    print_job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("print_jobs.id"), nullable=False, index=True)
    event_type: Mapped[PrinterEventType] = mapped_column(SqlEnum(PrinterEventType), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    print_job: Mapped[PrintJob] = relationship(back_populates="events")


class Notification(Timestamped, Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = uuid_primary_key()
    print_job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("print_jobs.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FormSubmission(Timestamped, Base):
    __tablename__ = "form_submissions"

    id: Mapped[uuid.UUID] = uuid_primary_key()
    experiment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experiments.id"), nullable=False, index=True)
    sample_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("samples.id"), nullable=False, index=True)
    form_type: Mapped[str] = mapped_column(String(100), nullable=False)
    values: Mapped[dict] = mapped_column(JSON, nullable=False)
