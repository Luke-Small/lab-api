from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


def setup_module() -> None:
    Base.metadata.create_all(bind=engine)


def teardown_module() -> None:
    Base.metadata.drop_all(bind=engine)


def test_experiment_to_notification_to_form_submission() -> None:
    client = TestClient(app)

    experiment = client.post("/api/v1/experiments", json={"name": "GelMA viability study"})
    assert experiment.status_code == 201
    experiment_id = experiment.json()["id"]

    sample = client.post(
        "/api/v1/samples",
        json={"experiment_id": experiment_id, "label": "Sample A", "barcode": "BIO-001"},
    )
    assert sample.status_code == 201
    sample_id = sample.json()["id"]

    print_job = client.post(
        "/api/v1/print-jobs",
        json={"experiment_id": experiment_id, "sample_id": sample_id, "name": "Kidney scaffold A"},
    )
    assert print_job.status_code == 201
    print_job_id = print_job.json()["id"]
    assert print_job.json()["status"] == "queued"

    event = client.post(
        f"/api/v1/print-jobs/{print_job_id}/events",
        headers={"Idempotency-Key": "printer-event-001"},
        json={"event_type": "completed", "details": {"duration_seconds": 245}},
    )
    assert event.status_code == 201
    assert event.json()["event_type"] == "completed"

    duplicate = client.post(
        f"/api/v1/print-jobs/{print_job_id}/events",
        headers={"Idempotency-Key": "printer-event-001"},
        json={"event_type": "completed", "details": {"duration_seconds": 245}},
    )
    assert duplicate.status_code == 201
    assert duplicate.json()["id"] == event.json()["id"]

    job_after_event = client.get(f"/api/v1/print-jobs/{print_job_id}")
    assert job_after_event.json()["status"] == "completed"

    notifications = client.get("/api/v1/notifications")
    assert notifications.status_code == 200
    assert len(notifications.json()) == 1
    assert "completed" in notifications.json()[0]["title"]

    form_submission = client.post(
        "/api/v1/form-submissions",
        json={
            "experiment_id": experiment_id,
            "sample_id": sample_id,
            "form_type": "post_print_observation",
            "values": {"construct_intact": True, "notes": "No visible defects."},
        },
    )
    assert form_submission.status_code == 201
    assert form_submission.json()["values"]["construct_intact"] is True
