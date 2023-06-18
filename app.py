from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import road, analyse
from database import get_db

# Создание экземпляра приложения FastAPI
app = FastAPI()
app.include_router(road.router)
app.include_router(analyse.router)

# Добавление CORS-мидлвары
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники
    allow_methods=["*"],  # Разрешаем все HTTP-методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

# Подключение к базе данных

# Пример маршрута
@app.get("/")
def read_root():
    # переадресация на маршрут /docs
    return {'message': 'Redirecting to /docs'}
