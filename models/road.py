from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from geoalchemy2 import Geometry
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import JSONB


Base = declarative_base()


class Road(Base):
    __tablename__ = 'roads'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    geometry = Column(Geometry(geometry_type='LINESTRING'))
    attributes = Column(JSONB)
    
    class Config:
        orm_mode = True


class RoadBase(BaseModel):
    name: str
    geometry: str
    attributes: dict


class RoadCreate(RoadBase):
    pass


class RoadUpdate(RoadBase):
    pass


class RoadInDB(RoadBase):
    id: int

    class Config:
        orm_mode = True
