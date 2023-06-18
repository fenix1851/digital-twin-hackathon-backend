from sqlalchemy.orm import Session
from typing import List
import requests
import logging
import io
import os
import sys
import requests
import hashlib
from utils import geoparse, get_address_by_cadastre_number
from sqlalchemy import func
from sqlalchemy.sql import expression
from geoalchemy2 import functions
from models.objects import Object, ObjectType
from math import cos, radians
from pymongo import MongoClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

mongo_client = MongoClient('mongodb://mongo:27017/')
db = mongo_client['osm']
cache_collection = db['cache']

class AnalyseRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_analys_by_cadstre_list(self, cadstre_list: str):
        cadastre_list = cadstre_list.split(';')
        cadastre_list = list(set(cadastre_list))  
        analyse_data = {}  
        for cadastre in cadastre_list:
            cadastre_hash = hashlib.sha256(cadastre.encode()).hexdigest()
            data = cache_collection.find_one({'cadastre_hash': cadastre_hash})
            if data:
                analyse_data[cadastre_hash] = data.get('data')
                continue


            analyse_data[cadastre_hash] = {}
            analyse_data[cadastre_hash]['address'] = get_address_by_cadastre_number.get_address_by_cadastre_number(cadastre)
            # analyse_data[cadastre_hash]['address'] = 'Краснодарский край, город Краснодар, улица Красная, дом 1'
            
            if analyse_data[cadastre_hash]['address'] == 'Неверный кадастровый номер':
                analyse_data[cadastre_hash] = {'address': 'Краснодарский край, г.Краснодар, Центральный округ, ул.Красноармейская, д.68'}
            analyse_data[cadastre_hash]['coordinates'] = geoparse.get_coordinates(analyse_data[cadastre_hash]['address'])
            # analyse_data[cadastre_hash]['coordinates'] = {'latitude': 45.035470, 'longitude': 38.976080}
            
            # Выполнение запроса на поиск объектов в радиусе 500 метров от заданной точки
            lat = analyse_data[cadastre_hash]['coordinates']['latitude']
            lon = analyse_data[cadastre_hash]['coordinates']['longitude']
            # Радиус в метрах
            radius_meters = 750

            # Конверсия радиуса из метров в градусы
            radius_degrees = radius_meters / (111.32 * 1000)
            # print(radius_degrees)
            # Использование сконвертированного радиуса в запросе
            nearby_objects = self.db.query(Object).filter(
                functions.ST_DWithin(
                    Object.geometry,
                    functions.ST_MakePoint(lon, lat),
                    radius_degrees
                )
            ).all()
        

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
            if len(nearby_objects) > 0:
                max_commercial_points = 650
                max_social_points = 650
                total_commercial_points = 0
                total_social_points = 0
                total_traffic = 0
                social_traffic = 0
                commercial_traffic = 0
                for category in analyse_data[cadastre_hash]['nearby_objects']:
                    total_commercial_points += analyse_data[cadastre_hash]['nearby_objects'][category]['commercial_points']
                    total_social_points += analyse_data[cadastre_hash]['nearby_objects'][category]['social_points']
                    total_traffic += analyse_data[cadastre_hash]['nearby_objects'][category]['weekly_visitors']
                    # print(category)
                    if analyse_data[cadastre_hash]['nearby_objects'][category]['commercial_points'] > analyse_data[cadastre_hash]['nearby_objects'][category]['social_points']:
                        social_traffic += analyse_data[cadastre_hash]['nearby_objects'][category]['weekly_visitors']
                    else:
                        commercial_traffic += analyse_data[cadastre_hash]['nearby_objects'][category]['weekly_visitors']

                
                commercial_percentage = (total_commercial_points / max_commercial_points) * 100
                social_percentage = (total_social_points / max_social_points) * 100

                commercial_percentage = round(commercial_percentage, 2)
                social_percentage = round(social_percentage, 2)

                # Сохранение найденных объектов и аналитических данных
                analyse_data[cadastre_hash]['scoring'] = {}
                analyse_data[cadastre_hash]['scoring'] = {
                    'commercial_percentage': commercial_percentage,
                    'social_percentage': social_percentage,
                    'total_traffic': total_traffic,
                }
                analyse_data[cadastre_hash]['scoring']['traffic_distribution'] = {
                    'commercial_traffic': commercial_traffic,
                    'social_traffic': social_traffic,
                }
                if commercial_percentage > social_percentage:
                    analyse_data[cadastre_hash]['scoring']['suggest'] = 'commercial'
                else:
                    analyse_data[cadastre_hash]['scoring']['suggest'] = 'social'
                
                if total_traffic > 30000:
                    analyse_data[cadastre_hash]['scoring']['traffic'] = 'high'
                elif total_traffic > 10000:
                    analyse_data[cadastre_hash]['scoring']['traffic'] = 'medium'
                else:
                    analyse_data[cadastre_hash]['scoring']['traffic'] = 'low'
                if analyse_data[cadastre_hash]['scoring']['traffic'] == 'high' and analyse_data[cadastre_hash]['scoring']['suggest'] == 'commercial':
                    analyse_data[cadastre_hash]['scoring']['suggest'] = 'Торговый центр'
                elif analyse_data[cadastre_hash]['scoring']['traffic'] == 'high' and analyse_data[cadastre_hash]['scoring']['suggest'] == 'social':
                    analyse_data[cadastre_hash]['scoring']['suggest'] = 'Развлекательный центр'
                elif analyse_data[cadastre_hash]['scoring']['traffic'] == 'medium' and analyse_data[cadastre_hash]['scoring']['suggest'] == 'commercial':
                    analyse_data[cadastre_hash]['scoring']['suggest'] = 'Магазин'
                elif analyse_data[cadastre_hash]['scoring']['traffic'] == 'medium' and analyse_data[cadastre_hash]['scoring']['suggest'] == 'social':
                    analyse_data[cadastre_hash]['scoring']['suggest'] = 'Кафе'
                elif analyse_data[cadastre_hash]['scoring']['traffic'] == 'low' and analyse_data[cadastre_hash]['scoring']['suggest'] == 'commercial':
                    analyse_data[cadastre_hash]['scoring']['suggest'] = 'Магазин'
                elif analyse_data[cadastre_hash]['scoring']['traffic'] == 'low' and analyse_data[cadastre_hash]['scoring']['suggest'] == 'social':
                    analyse_data[cadastre_hash]['scoring']['suggest'] = 'Жилой дом'
                
                suggest = analyse_data[cadastre_hash]['scoring']['suggest']
                suggest_description = ''

                if suggest == 'Торговый центр':
                    suggest_description = 'Рекомендуется размещение торгового центра, исходя из высокого уровня трафика и высокой социальной активности в этом районе.'
                elif suggest == 'Развлекательный центр':
                    suggest_description = 'Рекомендуется размещение развлекательного центра, исходя из высокого уровня трафика и высокой социальной активности в этом районе.'
                elif suggest == 'Магазин':
                    suggest_description = 'Рекомендуется размещение магазина, исходя из умеренного уровня трафика и средней социальной активности в этом районе.'
                elif suggest == 'Кафе':
                    suggest_description = 'Рекомендуется размещение кафе, исходя из умеренного уровня трафика и средней социальной активности в этом районе.'
                elif suggest == 'Жилой дом':
                    suggest_description = 'Рекомендуется размещение жилого дома, исходя из низкого уровня трафика и высокой социальной активности в этом районе.'
                
                analyse_data[cadastre_hash]['scoring']['suggest_description'] = suggest_description

                cache_collection.insert_one({'cadastre_hash': cadastre_hash, 'data': analyse_data[cadastre_hash]})


            # Сохранение найденных объектов в аналитических данных
            # analyse_data[cadastre_hash]['nearby_objects'] = [obj.to_dict() for obj in nearby_objects]
            
        return analyse_data
    
    def get_analys_by_coords(self, x, y, radius=1000):
        # Выполнение запроса на поиск объектов в радиусе 500 метров от заданной точки
        lat = x
        lon = y
        
            
        # Радиус в метрах
        radius_meters = 750

        # Конверсия радиуса из метров в градусы
        radius_degrees = radius_meters / (111.32 * 1000)

        # Использование сконвертированного радиуса в запросе
        nearby_objects = self.db.query(Object).filter(
            functions.ST_DWithin(
                Object.geometry,
                functions.ST_MakePoint(lon, lat),
                radius_degrees
            )
        ).all()
        analyse_data = {}
        # Итерация по близлежащим объектам и вычисление суммы еженедельных посетителей, коммерческих и социальных точек
        category_cache = {}
        for obj in nearby_objects:
            obj = obj.to_dict()
            category_name = category_cache.get(obj['type_id'])
            if not category_name:
                category_name = self.db.query(ObjectType).filter(ObjectType.id == obj['type_id']).first().name
                category_cache[obj['type_id']] = category_name
            if not analyse_data.get('nearby_objects'):
                analyse_data['nearby_objects'] = {}
            if not analyse_data['nearby_objects'].get(category_name):
                analyse_data['nearby_objects'][category_name] = {}
                analyse_data['nearby_objects'][category_name]['weekly_visitors'] = 0
                analyse_data['nearby_objects'][category_name]['commercial_points'] = 0
                analyse_data['nearby_objects'][category_name]['social_points'] = 0
                analyse_data['nearby_objects'][category_name]['count'] = 0
            analyse_data['nearby_objects'][category_name]['weekly_visitors'] += obj['weekly_visitors']
            analyse_data['nearby_objects'][category_name]['commercial_points'] += obj['commercial_points']
            analyse_data['nearby_objects'][category_name]['social_points'] += obj['social_points']
            analyse_data['nearby_objects'][category_name]['count'] += 1

            analyse_data['coordinates'] = {
                'latitude': lat,
                'longitude': lon
            }
        if len(nearby_objects) > 0:
            max_commercial_points = 650
            max_social_points = 650
            total_commercial_points = 0
            total_social_points = 0
            total_traffic = 0
            social_traffic = 0
            commercial_traffic = 0

            for category in analyse_data['nearby_objects']:
                total_commercial_points += analyse_data['nearby_objects'][category]['commercial_points']
                total_social_points += analyse_data['nearby_objects'][category]['social_points']
                total_traffic += analyse_data['nearby_objects'][category]['weekly_visitors']

                if analyse_data['nearby_objects'][category]['commercial_points'] > analyse_data['nearby_objects'][category]['social_points']:
                    social_traffic += analyse_data['nearby_objects'][category]['weekly_visitors']
                else:
                    commercial_traffic += analyse_data['nearby_objects'][category]['weekly_visitors']

            commercial_percentage = (total_commercial_points / max_commercial_points) * 100
            social_percentage = (total_social_points / max_social_points) * 100

            commercial_percentage = round(commercial_percentage, 2)
            social_percentage = round(social_percentage, 2)

            # Сохранение найденных объектов и аналитических данных
            scoring_data = {
                'commercial_percentage': commercial_percentage,
                'social_percentage': social_percentage,
                'total_traffic': total_traffic,
                'traffic_distribution': {
                    'commercial_traffic': commercial_traffic,
                    'social_traffic': social_traffic,
                },
                'suggest_description': '',
            }

            if commercial_percentage > social_percentage:
                scoring_data['suggest'] = 'commercial'
            else:
                scoring_data['suggest'] = 'social'

            if total_traffic > 30000:
                scoring_data['traffic'] = 'high'
            elif total_traffic > 10000:
                scoring_data['traffic'] = 'medium'
            else:
                scoring_data['traffic'] = 'low'

            if scoring_data['traffic'] == 'high' and scoring_data['suggest'] == 'commercial':
                scoring_data['suggest'] = 'Торговый центр'
            elif scoring_data['traffic'] == 'high' and scoring_data['suggest'] == 'social':
                scoring_data['suggest'] = 'Развлекательный центр'
            elif scoring_data['traffic'] == 'medium' and scoring_data['suggest'] == 'commercial':
                scoring_data['suggest'] = 'Магазин'
            elif scoring_data['traffic'] == 'medium' and scoring_data['suggest'] == 'social':
                scoring_data['suggest'] = 'Кафе'
            elif scoring_data['traffic'] == 'low' and scoring_data['suggest'] == 'commercial':
                scoring_data['suggest'] = 'Магазин'
            elif scoring_data['traffic'] == 'low' and scoring_data['suggest'] == 'social':
                scoring_data['suggest'] = 'Жилой дом'

            suggest_description = scoring_data['suggest_description']
            suggest = scoring_data['suggest']

            if suggest == 'Торговый центр':
                suggest_description = 'Рекомендуется размещение торгового центра, исходя из высокого уровня трафика и высокой социальной активности в этом районе.'
            elif suggest == 'Развлекательный центр':
                suggest_description = 'Рекомендуется размещение развлекательного центра, исходя из высокого уровня трафика и высокой социальной активности в этом районе.'
            elif suggest == 'Магазин':
                suggest_description = 'Рекомендуется размещение магазина, исходя из умеренного уровня трафика и средней социальной активности в этом районе.'
            elif suggest == 'Кафе':
                suggest_description = 'Рекомендуется размещение кафе, исходя из умеренного уровня трафика и средней социальной активности в этом районе.'
            elif suggest == 'Жилой дом':
                suggest_description = 'Рекомендуется размещение жилого дома, исходя из низкого уровня трафика и высокой социальной активности в этом районе.'

            scoring_data['suggest_description'] = suggest_description

            analyse_data['scoring'] = scoring_data
        
        return analyse_data



    def get_photo_url_by_prompt(self, prompt):
        url = 'https://stablediffusionapi.com/api/v3/text2img'
        headers = {
            'Content-Type': 'application/json'
        }
        print(prompt)
        data = {
            "key": "nAytUPMXhmmG1zdgySwsFW35YuVasrhQINRZrHxToPRqrATMAXZqkBRtEotA",
            "prompt": prompt['prompt'],
            "negative_prompt": None,
            "width": "512",
            "height": "512",
            "samples": "1",
            "num_inference_steps": "20",
            "safety_checker": "no",
            "enhance_prompt": "yes",
            "seed": None,
            "guidance_scale": 7.5,
            "multi_lingual": "no",
            "panorama": "no",
            "self_attention": "no",
            "upscale": "no",
            "embeddings_model": "embeddings_model_id",
            "webhook": None,
            "track_id": None
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response_data = response.json()
            print(response_data)
            photo_url = response_data['output'][0]
        except:
            from_db = cache_collection.find_one({'prompt': prompt})
            if from_db:
                photo_url = from_db['photo_url']
            else:
                photo_url = 'https://i.imgur.com/5Qz9qRf.jpg'

        # write to file
        cache_collection.insert_one({
            'prompt': prompt,
            'photo_url': photo_url
        })

        return photo_url




