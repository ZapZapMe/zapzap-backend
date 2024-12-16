from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from databases import database
# use Sqlite for now
DATABASE_URL = "sqlite:///./test.db"
#DATABASE_URL = ""

# SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Async Database
database = Database(DATABASE_URL)

#Initialize the database tables
def init_db():
    from app.db.models import Base
    Base.metadata.create_all(bind=engine)