from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.constants.messages import AUDIT_ACTIONS
from app.log_helpers import audit_event
from app.middlewares.quota import quota_snapshot
from app.models import User
from app.schemas.dataset import serialize_dataset
from app.services import dataset_service, profile_service, run_service


def list_datasets(db: Session, user: User) -> dict:
    datasets = dataset_service.list_datasets(db)
    return {
        "items": [dataset_service.serialize(db, dataset) for dataset in datasets],
        "total": len(datasets),
        "quota": quota_snapshot(user),
    }


async def upload(request, db: Session, user: User, file: UploadFile) -> dict:
    payload = await file.read()
    dataset, created = dataset_service.upsert_dataset(db, user, file.filename, payload)
    run = profile_service.start_profile(db, user, dataset)
    run_service.dispatch_profile_run(run.id)
    audit_event(
        request,
        AUDIT_ACTIONS["DATASET_UPLOAD"],
        "Dataset",
        dataset.id,
        None,
        {
            "name": dataset.name,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "checksum": dataset.checksum,
            "created": created,
        },
    )
    return {
        "dataset": dataset_service.serialize(db, dataset),
        "profile_run_id": run.id,
        "created": created,
        "quota": quota_snapshot(user),
    }


def get_dataset(db: Session, dataset_id: int) -> dict:
    dataset = dataset_service.get_dataset(db, dataset_id)
    return dataset_service.serialize(db, dataset)


def delete_dataset(request, db: Session, user: User, dataset_id: int) -> dict:
    dataset = dataset_service.get_dataset(db, dataset_id)
    before = dataset_service.delete_dataset(db, dataset, user)
    audit_event(request, AUDIT_ACTIONS["DATASET_DELETE"], "Dataset", dataset_id, before, None)
    return {"deleted": True, "dataset_id": dataset_id}
