from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers import dataset_controller
from app.middlewares.auth import get_current_user
from app.middlewares.rbac import require_roles
from app.models import User
from app.services import dataset_service

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("")
def list_datasets(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return dataset_controller.list_datasets(db, user)


@router.post("/upload")
async def upload(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("steward", "analyst")),
):
    return await dataset_controller.upload(request, db, user, file)


@router.get("/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return dataset_controller.get_dataset(db, dataset_id)


@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("steward")),
):
    return dataset_controller.delete_dataset(request, db, user, dataset_id)


@router.get("/{dataset_id}/download")
def download_dataset(dataset_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    dataset = dataset_service.get_dataset(db, dataset_id)
    return FileResponse(dataset.file_path, filename=dataset.name)
