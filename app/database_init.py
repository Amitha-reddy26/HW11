from app.db.base import Base
from app.models import user
from app.database import engine
     

def init_db():
    Base.metadata.create_all(bind=engine)

def drop_db():
    Base.metadata.drop_all(bind=engine)

if __name__ == "__main__":
    init_db()  # pragma: no cover
