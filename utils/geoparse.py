from geopy.geocoders import GoogleV3
import random

API_KEY = 'AIzaSyA2L7YXJknDDK-Z-LfuNeUvxaje-YFPdn0'  # Замените на свой ключ API от Google

def get_coordinates(address: str) -> dict:
    geolocator = GoogleV3(api_key=API_KEY)  # Создание экземпляра геокодера GoogleV3

    # Сначала попытка геокодировать полный адрес
    location = geolocator.geocode(address)

    # Если геокодирование не удалось, убрать детали адреса и попробовать снова
    if location is None:
        address.replace('пгт', 'п')
        address.replace('поселок городского типа', 'п')
        address.replace('поселок', 'п')
        address.replace('с/о', 'п')
        parts = address.split(',')

        if len(parts) > 3:
            for i in range(len(parts), 2, -1):
                new_address = ','.join(parts[:i])
                location = geolocator.geocode(new_address)
                if location is not None:
                    break
    
    # Обработка ситуации, когда геокодирование не удалось даже после удаления деталей
    if location is None:
        bounding_box = geolocator.geocode("Краснодарский край, Россия")
        return {
            "latitude": bounding_box.latitude + random.uniform(-0.1, 0.1),
            "longitude": bounding_box.longitude + random.uniform(-0.1, 0.1),
            "is_fake": True,
        }

    # Извлечение географических координат
    latitude = location.latitude
    longitude = location.longitude

    return {
        "latitude": latitude,
        "longitude": longitude,
        "is_fake": False,
    }

print(get_coordinates('Краснодарский край, городской округ Сочи, город Сочи, улица Конституции СССР, 1'))
