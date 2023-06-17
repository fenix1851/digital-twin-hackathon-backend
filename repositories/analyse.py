from sqlalchemy.orm import Session
from typing import List
import requests
import logging
import io
import os
import sys
import hashlib
from utils import geoparse, get_address_by_cadastre_number
from sqlalchemy import func
from sqlalchemy.sql import expression
from geoalchemy2 import functions
from models.objects import Object, ObjectType
from math import cos, radians


class AnalyseRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_analys_by_cadstre_list(self, cadstre_list: str):
        cadastre_list = cadstre_list.split(';')
        cadastre_list = list(set(cadastre_list))  
        analyse_data = {}  
        for cadastre in cadastre_list:
            cadastre_hash = hashlib.sha256(cadastre.encode()).hexdigest()
            analyse_data[cadastre_hash] = {}
            analyse_data[cadastre_hash]['address'] = get_address_by_cadastre_number.get_address_by_cadastre_number(cadastre)
            # analyse_data[cadastre_hash]['address'] = 'Краснодарский край, город Краснодар, улица Красная, дом 1'
            
            if analyse_data[cadastre_hash]['address'] == 'Неверный кадастровый номер':
                analyse_data[cadastre_hash] = {'address': 'Краснодарский край, город Краснодар, улица Красная, дом 1'}
                continue
            analyse_data[cadastre_hash]['coordinates'] = geoparse.get_coordinates(analyse_data[cadastre_hash]['address'])
            # analyse_data[cadastre_hash]['coordinates'] = {'latitude': 45.035470, 'longitude': 38.976080}
            
            # Выполнение запроса на поиск объектов в радиусе 500 метров от заданной точки
            lat = analyse_data[cadastre_hash]['coordinates']['latitude']
            lon = analyse_data[cadastre_hash]['coordinates']['longitude']
            # Радиус в метрах
            radius_meters = 500

            # Конверсия радиуса из метров в градусы
            radius_degrees = radius_meters / (111.32 * 1000)
            print(radius_degrees)
            # Использование сконвертированного радиуса в запросе
            nearby_objects = self.db.query(Object).filter(
                functions.ST_DWithin(
                    Object.geometry,
                    functions.ST_MakePoint(lon, lat),
                    radius_degrees
                )
            ).all()
            print(len(nearby_objects))
            if(len(nearby_objects) == 3492):
                return {'error': 'Too many objects in radius'}

            # iterate over nearby_objects and calculate sum of weekly_visitors, commercial_points, social_points
            category_cache = {}
            for obj in nearby_objects:
                obj = obj.to_dict()
                if not analyse_data[cadastre_hash].get('nearby_objects'):
                    analyse_data[cadastre_hash]['nearby_objects'] = {}
                category_name = category_cache.get(obj['type_id'])
                if not category_name:
                    category_name = self.db.query(ObjectType).filter(ObjectType.id == obj['type_id']).first().name
                    category_cache[obj['type_id']] = category_name
                if not analyse_data[cadastre_hash]['nearby_objects'].get(category_name):
                    analyse_data[cadastre_hash]['nearby_objects'][category_name] = {}
                    analyse_data[cadastre_hash]['nearby_objects'][category_name]['weekly_visitors'] = 0
                    analyse_data[cadastre_hash]['nearby_objects'][category_name]['commercial_points'] = 0
                    analyse_data[cadastre_hash]['nearby_objects'][category_name]['social_points'] = 0
                    analyse_data[cadastre_hash]['nearby_objects'][category_name]['count'] = 0
                analyse_data[cadastre_hash]['nearby_objects'][category_name]['weekly_visitors'] += obj['weekly_visitors']
                analyse_data[cadastre_hash]['nearby_objects'][category_name]['commercial_points'] += obj['commercial_points']
                analyse_data[cadastre_hash]['nearby_objects'][category_name]['social_points'] += obj['social_points']
                analyse_data[cadastre_hash]['nearby_objects'][category_name]['count'] += 1


            # Сохранение найденных объектов в аналитических данных
            # analyse_data[cadastre_hash]['nearby_objects'] = [obj.to_dict() for obj in nearby_objects]
            
        return analyse_data

