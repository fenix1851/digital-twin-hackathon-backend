from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from repositories.analyse import AnalyseRepository
from models.road import Road, RoadInDB
from database.get_db import get_db

from typing import List
from pydantic import BaseModel

router = APIRouter()


class CadstreRequest(BaseModel):
    kadastrovyyKod: str

class CoordsRequest(BaseModel):
    x: float
    y: float

@router.post("/get_analys_by_cadstre_list")
def get_analys_by_cadstre_list(request: CadstreRequest, db: Session = Depends(get_db)):
    kadastrovyy_kod = request.kadastrovyyKod
    print(kadastrovyy_kod)
    road_repo = AnalyseRepository(db)
    analysis = road_repo.get_analys_by_cadstre_list(kadastrovyy_kod)
    return analysis

@router.post("/get_analys_by_coords")
def get_analys_by_coords(request: CoordsRequest, db: Session = Depends(get_db)):
    x = request.x
    y = request.y
    print(x, y)
    road_repo = AnalyseRepository(db)
    analysis = road_repo.get_analys_by_coords(x, y)
    return analysis

@router.post("/get_photo_url_by_prompt")
def get_photo_url_by_prompt(dict: dict, db: Session = Depends(get_db)):
    road_repo = AnalyseRepository(db)
    photo_url = road_repo.get_photo_url_by_prompt(dict)
    return photo_url
