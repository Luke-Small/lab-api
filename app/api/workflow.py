from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.workflow import (
    Experiment,
    FormSubmission,
    Notification,
    PrinterEvent,
    PrinterEventType,
    PrintJob,
    PrintJobStatus,
    Sample,
)
from app.schemas.workflow import (
    ExperimentCreate,
    ExperimentRead,
    FormSubmissionCreate,
    FormSubmissionRead,
    NotificationRead,
    PrinterEventCreate,
    PrinterEventRead,
    PrintJobCreate,
    PrintJobRead,
    SampleCreate,
    SampleRead,
)

router = APIRouter(prefix="/api/v1", tags=["workflow"])


def _required(model, identifier: UUID, database: Session):
    value = database.get(model, identifier)
    if value is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found")
    return value


@router.post("/experiments", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
def create_experiment(payload: ExperimentCreate, database: Session = Depends(get_db)):
    experiment = Experiment(**payload.model_dump())
    database.add(experiment)
    database.commit()
    database.refresh(experiment)
    return experiment


@router.get("/experiments/{experiment_id}", response_model=ExperimentRead)
def get_experiment(experiment_id: UUID, database: Session = Depends(get_db)):
    return _required(Experiment, experiment_id, database)


@router.post("/samples", response_model=SampleRead, status_code=status.HTTP_201_CREATED)
def create_sample(payload: SampleCreate, database: Session = Depends(get_db)):
    _required(Experiment, payload.experiment_id, database)
    sample = Sample(**payload.model_dump())
    database.add(sample)
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sample barcode already exists") from error
    database.refresh(sample)
    return sample


@router.post("/print-jobs", response_model=PrintJobRead, status_code=status.HTTP_201_CREATED)
def create_print_job(payload: PrintJobCreate, database: Session = Depends(get_db)):
    _required(Experiment, payload.experiment_id, database)
    sample = _required(Sample, payload.sample_id, database)
    if sample.experiment_id != payload.experiment_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Sample does not belong to experiment")
    print_job = PrintJob(**payload.model_dump())
    database.add(print_job)
    database.commit()
    database.refresh(print_job)
    return print_job


@router.get("/print-jobs/{print_job_id}", response_model=PrintJobRead)
def get_print_job(print_job_id: UUID, database: Session = Depends(get_db)):
    return _required(PrintJob, print_job_id, database)


@router.post("/print-jobs/{print_job_id}/events", response_model=PrinterEventRead, status_code=status.HTTP_201_CREATED)
def create_printer_event(
    print_job_id: UUID,
    payload: PrinterEventCreate,
    idempotency_key: str = Header(min_length=1, max_length=200),
    database: Session = Depends(get_db),
):
    print_job = _required(PrintJob, print_job_id, database)
    existing = database.scalar(
        select(PrinterEvent).where(
            PrinterEvent.print_job_id == print_job_id,
            PrinterEvent.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        return existing

    status_for_event = {
        PrinterEventType.started: PrintJobStatus.running,
        PrinterEventType.completed: PrintJobStatus.completed,
        PrinterEventType.failed: PrintJobStatus.failed,
    }
    print_job.status = status_for_event[payload.event_type]
    event = PrinterEvent(print_job_id=print_job_id, idempotency_key=idempotency_key, **payload.model_dump())
    notification = Notification(
        print_job_id=print_job_id,
        title=f"Print job {print_job.status.value}",
        body=f"{print_job.name}: printer reported {payload.event_type.value}.",
    )
    database.add_all([event, notification])
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate printer event") from error
    database.refresh(event)
    return event


@router.get("/notifications", response_model=list[NotificationRead])
def list_notifications(database: Session = Depends(get_db)):
    return list(database.scalars(select(Notification).order_by(Notification.created_at.desc())))


@router.post("/notifications/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(notification_id: UUID, database: Session = Depends(get_db)):
    notification = _required(Notification, notification_id, database)
    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        database.commit()
        database.refresh(notification)
    return notification


@router.post("/form-submissions", response_model=FormSubmissionRead, status_code=status.HTTP_201_CREATED)
def create_form_submission(payload: FormSubmissionCreate, database: Session = Depends(get_db)):
    _required(Experiment, payload.experiment_id, database)
    sample = _required(Sample, payload.sample_id, database)
    if sample.experiment_id != payload.experiment_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Sample does not belong to experiment")
    submission = FormSubmission(**payload.model_dump())
    database.add(submission)
    database.commit()
    database.refresh(submission)
    return submission
