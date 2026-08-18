from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.workflow import PrinterEventType, PrintJobStatus


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ExperimentRead(ApiModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime


class SampleCreate(BaseModel):
    experiment_id: UUID
    label: str = Field(min_length=1, max_length=200)
    barcode: str | None = Field(default=None, max_length=200)


class SampleRead(ApiModel):
    id: UUID
    experiment_id: UUID
    label: str
    barcode: str | None
    created_at: datetime


class PrintJobCreate(BaseModel):
    experiment_id: UUID
    sample_id: UUID
    name: str = Field(min_length=1, max_length=200)


class PrintJobRead(ApiModel):
    id: UUID
    experiment_id: UUID
    sample_id: UUID
    name: str
    status: PrintJobStatus
    created_at: datetime


class PrinterEventCreate(BaseModel):
    event_type: PrinterEventType
    details: dict[str, Any] = Field(default_factory=dict)


class PrinterEventRead(ApiModel):
    id: UUID
    print_job_id: UUID
    event_type: PrinterEventType
    details: dict[str, Any]
    created_at: datetime


class NotificationRead(ApiModel):
    id: UUID
    print_job_id: UUID
    title: str
    body: str
    read_at: datetime | None
    created_at: datetime


class FormSubmissionCreate(BaseModel):
    experiment_id: UUID
    sample_id: UUID
    form_type: str = Field(min_length=1, max_length=100)
    values: dict[str, Any]


class FormSubmissionRead(ApiModel):
    id: UUID
    experiment_id: UUID
    sample_id: UUID
    form_type: str
    values: dict[str, Any]
    created_at: datetime
