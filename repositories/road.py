from sqlalchemy.orm import Session
from models.road import Road
from models.objects import Object, ObjectType
from typing import List
import requests
from lxml import etree
import logging
import io
import os
import sys
from pymongo import MongoClient
import urllib3
import random
import json
from geoalchemy2 import functions

# Подавление предупреждений urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

mongo_client = MongoClient('mongodb://mongo:27017/')
db = mongo_client['osm']
way_collection = db['ways']

class RoadRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_roads(self) -> List[Road]:
        return self.db.query(Road).all() 
    
    def parse_roads(self) -> List[Road]:
        roads = []
        chunk_size = 10000
        documents_count = way_collection.count_documents({})
        rounds_count = documents_count // chunk_size + 1
        count_of_parsed_roads = 0
        while rounds_count > 0:
            offset = (rounds_count - 1) * chunk_size
            rounds_count -= 1
            ways = way_collection.find({}).skip(offset).limit(chunk_size)
            print(ways)
            for way in ways:
                print(way)
                name = way['tags'].get('name')
                print(f'Road {name} is parsing')
                print(way['tags'])
                nodes = way['nodes']
                
                geometry = 'LINESTRING(' + ', '.join([f"{float(node['lon'])} {float(node['lat'])}" for node in nodes]) + ')'
                
                attributes = {
                    'highway': way['tags'].get('highway'),
                    'name': name,
                    'name:en': way['tags'].get('name:en'),
                    'name:ru': way['tags'].get('name:ru')
                }
                if(attributes['highway'] == None) or (attributes['name'] == None):
                    print(f'Road {name} is skipped')
                    continue
                road = Road(name=name, geometry=geometry, attributes=attributes)
                print(f'Road {road.name} is done')
                roads.append(road)
                count_of_parsed_roads += 1
            # self.db.bulk_save_objects(roads)
            # self.db.commit()
            roads = []
            print(f'Round {rounds_count} of {rounds_count} is done')
        print(f'Count of parsed roads: {count_of_parsed_roads}')
        
        return roads
    
    def generateObjects(self):
        roads = self.db.query(Road).all()
        object_counts = {
            'Школа': 150,
            'Больница': 20,
            'Торговый центр': 30,
            'Остановка общественного транспорта': 500,
            'Парк': 40,
            'Стадион': 5,
            'Библиотека': 25,
            'Университет': 10,
            'Полицейский участок': 15,
            'Пожарная часть': 10,
            'Ресторан': 200,
            'Аптека': 100,
            'Музей': 10,
            'Кинотеатр': 15,
            'Театр': 5,
            'Кафе': 500,
            'Гостиница': 50,
            'Банк': 30,
            'Почтовое отделение': 50,
            'Супермаркет': 100,
            'Спортивный комплекс': 15,
            'Автовокзал': 5,
            'Железнодорожный вокзал': 3,
            'Мэрия': 1,
            'Парикмахерская/салон красоты': 300,
            'Автосервис': 50,
            'Аэропорт': 1,
            'Магазин одежды': 200,
            'Магазин электроники': 50,
            'Пляж': 5,
            'Рынок': 30,
            'Парковка': 500,
            'Аттракционный парк': 2,
            'Зоопарк': 1,
            'Посольство': 1,
            'Конференц-центр': 5,
            'Выставочный центр': 10,
            'Спортивный клуб/фитнес-центр': 100,
            'Религиозное сооружение': 50,
            'Парковая зона': 50,
            'Детский сад': 100,
            'Место для пикника': 30,
            'Место для гриля/барбекю': 20,
            'Бассейн': 10,
            'Станция метро': 0,
            'Суд/трибунал': 5,
            'Ветеринарная клиника': 50,
            'Фармацевтическая компания': 10,
            'Туристический информационный центр': 3,
            'Многофункциональный комплекс': 20
        }

        objects = []
        for object_type, count in object_counts.items():
            for i in range(count):
                road = random.choice(roads)
                print(f'Object {object_type} {i} is generating')
                coordinates = f"{road.geometry.y};{road.geometry.x}"  # Concatenate latitude and longitude
                object_type_db = self.db.query(ObjectType).filter(ObjectType.name == object_type).first()
                if object_type_db:
                    object = Object(
                        name=f'{object_type} {i}',
                        commercial_points=random.randint(0, 10),
                        social_points=random.randint(0, 10),
                        type_id=object_type_db.id,
                        geometry=road.geometry,  # Use the original geometry (WKBElement)
                        attributes={},
                        coordinates=coordinates,
                        weekly_visitors=random.randint(100, 1000)
                    )
                    objects.append(object)
                    print(f'Object {object.name} is done')
                    print(object.__dict__)
        # self.db.bulk_save_objects(objects)
        # self.db.commit()
        print(f'Count of generated objects: {len(objects)}')
        return 'Done'
