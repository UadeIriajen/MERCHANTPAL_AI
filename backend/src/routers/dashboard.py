from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.dependencies import get_db
from src.repository.dashboard_repository import DashboardRepository
from src.schemas.dashboard import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_statistics(db: Session = Depends(get_db)) -> DashboardStats:
    return DashboardRepository(db).get_stats()
