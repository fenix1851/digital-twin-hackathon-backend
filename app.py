from fastapi import FastAPI
from routers import road, analyse
from database import get_db

# Создание экземпляра приложения FastAPI
app = FastAPI()
app.include_router(road.router)
app.include_router(analyse.router)
# Подключение к базе данных


# Пример маршрута
@app.get("/")
def read_root():
    # переадресация на маршрут /docs
    return '/docs'
    

