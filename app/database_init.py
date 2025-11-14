from app.database import engine
from app.schemas.base import Base  
from app.models import user       

def init_db():
    Base.metadata.create_all(bind=engine)

def drop_db():
    Base.metadata.drop_all(bind=engine)

if __name__ == "__main__":
    init_db()  # pragma: no cover
