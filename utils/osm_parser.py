import os
import json
import xml.etree.ElementTree as ET
from pymongo import MongoClient
import urllib3

# Подавление предупреждений urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Подключение к MongoDB
mongo_client = MongoClient('mongodb://mongo:27017/')  # Используйте имя сервиса контейнера MongoDB из docker-compose.yml
db = mongo_client['osm']  # Замените 'mydatabase' на имя вашей базы данных MongoDB
collection = db['nodes']  # Замените 'nodes' на имя вашей коллекции MongoDB
wayCollection = db['ways']
# Путь к папке с файлами OSM
osm_folder = 'src/osm'

filenames = os.listdir(osm_folder)
filenames_reverse = filenames[::-1]

# for filename in filenames_reverse:
#     print(f'Parsing {filename}...')
#     if filename.endswith('.osm'):
#         print(f'{filename} is osm file')
#         filepath = os.path.join(osm_folder, filename)
#         tree = ET.parse(filepath)
#         root = tree.getroot()

#         for node in root.findall('.//node'):
#             node_data = {
#                 'id': node.attrib['id'],
#                 'lat': node.attrib['lat'],
#                 'lon': node.attrib['lon'],
#                 'tags': {}
#             }
#             if node.findall('.//tag'):
#                 for tag in node.findall('.//tag'):
#                     node_data['tags'][tag.attrib['k']] = tag.attrib['v']
#             node_from_db = collection.find_one({'id': node.attrib['id']})
#             if node_from_db:
#                 print(f'Node {node.attrib["id"]} already exists in MongoDB')
#             else:
#                 collection.insert_one(node_data)
#                 print(f'Node {node.attrib["id"]} inserted into MongoDB')
#                 print(node_data)

from collections import defaultdict
from pymongo import UpdateOne

# Создаем пустые списки для сбора операций bulk_write
insert_operations = []
update_operations = []

# Создаем индекс на поле 'id' в коллекции wayCollection
wayCollection.create_index('id')

for filename in filenames_reverse:
    countofnodes = 0
    countofunsavednodes = 0
    countofways = 0
    countofupdatedways = 0
    print(f'Parsing {filename}...')
    
    if filename.endswith('.osm'):
        print(f'{filename} is osm file')
        filepath = os.path.join(osm_folder, filename)
        tree = ET.parse(filepath)
        root = tree.getroot()

        # Используем defaultdict для автоматического создания пустых списков
        way_data_dict = defaultdict(lambda: {
            'id': None,
            'nodes': [],
            'tags': {}
        })
        chunk_size = 1000
        for way in root.findall('.//way'):
            way_data = way_data_dict[way.attrib['id']]
            way_data['id'] = way.attrib['id']

            if way.findall('.//tag'):
                for tag in way.findall('.//tag'):
                    way_data['tags'][tag.attrib['k']] = tag.attrib['v']

            if way.findall('.//nd'):
                for nd in way.findall('.//nd'):
                    node_id = nd.attrib['ref']
                    node = collection.find_one({'id': node_id})
                    if node:
                        way_data['nodes'].append(node)
                        countofnodes += 1
                    else:
                        print(f'Node {node_id} not found')
                        countofunsavednodes += 1

        for way_id, way_data in way_data_dict.items():
            way_from_db = wayCollection.find_one({'id': way_id})

            if way_from_db:
                nodes = set(way_from_db['nodes'])
                new_nodes = set(way_data['nodes'])

                if new_nodes - nodes:
                    nodes.update(new_nodes)
                    update_operations.append(
                        UpdateOne({'id': way_id}, {'$set': {'nodes': list(nodes)}})
                    )
                    if(len(update_operations) >= chunk_size):
                        wayCollection.bulk_write(update_operations)
                        update_operations = []
                        print(f'Way {way_id} updated in MongoDB')
                    print(f'Way {way_id} already exists in MongoDB')
                    print(way_data)
                    countofupdatedways += 1
            else:
                insert_operations.append(way_data)
                if(len(insert_operations) >= chunk_size):
                    wayCollection.insert_many(insert_operations)
                    insert_operations = []
                    print(f'Way {way_id} inserted into MongoDB')
                print(f'Way {way_id} inserted into MongoDB')
                print(way_data)
                countofways += 1

        # Выполняем пакетную вставку и обновление операций
        if insert_operations:
            wayCollection.insert_many(insert_operations)
        if update_operations:
            wayCollection.bulk_write(update_operations)

        print(f'Count of nodes: {countofnodes}')
        print(f'Count of unsaved nodes: {countofunsavednodes}')
        print(f'Count of ways: {countofways}')
        print(f'Count of updated ways: {countofupdatedways}')


