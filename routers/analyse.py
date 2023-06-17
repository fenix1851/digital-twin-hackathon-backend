from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from repositories.analyse import AnalyseRepository
from models.road import Road, RoadInDB
from database.get_db import get_db

from typing import List

router = APIRouter()


@router.get("/get_analys_by_cadstre_list/{cadstre_list}")
def get_analys_by_cadstre_list(cadstre_list: str, db: Session = Depends(get_db)):
    road_repo = AnalyseRepository(db)
    analysis = road_repo.get_analys_by_cadstre_list(cadstre_list)
    return analysis

