from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class ObjectType(Base):
    __tablename__ = 'object_types'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)

    objects = relationship("Object", back_populates="object_type")


class Object(Base):
    __tablename__ = 'objects'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    commercial_points = Column(Integer)
    social_points = Column(Integer)
    type_id = Column(Integer, ForeignKey('object_types.id'))
    geometry = Column(Geometry(geometry_type='POINT'))
    attributes = Column(JSONB)
    coordinates = Column(String)  # Координаты школы
    weekly_visitors = Column(Integer) 
    object_type = relationship("ObjectType", back_populates="objects")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'commercial_points': self.commercial_points,
            'social_points': self.social_points,
            'type_id': self.type_id,
            # 'geometry': str(self.geometry),
            'attributes': self.attributes,
            'coordinates': self.coordinates,
            'weekly_visitors': self.weekly_visitors
        }



