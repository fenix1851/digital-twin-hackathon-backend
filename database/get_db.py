from starlette.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from configs.vars import DATABASE_URL
from models.road import Base
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(engine)
from models.objects import Base
Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()