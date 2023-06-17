from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from repositories.road import RoadRepository
from models.road import Road, RoadInDB
from database.get_db import get_db

from typing import List

router = APIRouter()


@router.get("/roads", response_model=List[RoadInDB])
def get_all_roads(db: Session = Depends(get_db)):
    road_repo = RoadRepository(db)
    roads = road_repo.get_all_roads()
    return roads

@router.get("/parse_roads")
def parse_roads(db: Session = Depends(get_db)):
    road_repo = RoadRepository(db)
    res =road_repo.parse_roads()
    return res

@router.get("/generateObjects")
def generate_objects(db: Session = Depends(get_db)):
    road_repo = RoadRepository(db)
    res =road_repo.generateObjects()
    return res

