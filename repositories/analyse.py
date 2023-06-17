from sqlalchemy.orm import Session
from typing import List
import requests
import logging
import io
import os
import sys
import hashlib
from utils import geoparse, get_address_by_cadastre_number

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
            if analyse_data[cadastre_hash]['address'] == 'Неверный кадастровый номер':
                analyse_data[cadastre_hash] = {'address': 'Краснодарский край, город Краснодар, улица Красная, дом 1'}
                continue
            analyse_data[cadastre_hash]['coordinates'] = geoparse.get_coordinates(analyse_data[cadastre_hash]['address'])
            
        return analyse_data
