from sqlalchemy.orm import Session

from app.constants.messages import AUDIT_ACTIONS
from app.log_helpers import audit_event
from app.middlewares.quota import quota_snapshot
from app.models import User
from app.services import dataset_service, profile_service, rule_service, run_service


def start_profile(request, db: Session, user: User, dataset_id: int) -> dict:
    dataset = dataset_service.get_dataset(db, dataset_id)
    run = profile_service.start_profile(db, user, dataset)
    run_service.dispatch_profile_run(run.id)
    audit_event(
        request, AUDIT_ACTIONS["PROFILE_RECOMPUTE"], "Dataset", dataset_id, None, {"run_id": run.id}
    )
    return {"run_id": run.id, "status": run.status, "quota": quota_snapshot(user)}


def get_profile(db: Session, dataset_id: int) -> dict:
    dataset = dataset_service.get_dataset(db, dataset_id)
    return profile_service.profile_payload(db, dataset)


def get_columns(db: Session, dataset_id: int) -> dict:
    payload = profile_service.profile_payload(db, dataset_service.get_dataset(db, dataset_id))
    return {
        "dataset_id": dataset_id,
        "columns": [
            {
                "column_name": column["column_name"],
                "inferred_type": column["inferred_type"],
                "type_label": column["type_label"],
                "null_rate": column["null_rate"],
                "distinct_count": column["distinct_count"],
            }
            for column in payload["columns"]
        ],
    }


def recommend(db: Session, dataset_id: int, limit: int = 5) -> dict:
    return {"items": rule_service.recommend(db, dataset_id, limit=limit)}
