from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# connection string example: mysql+mysqlconnector://user:password@localhost:3306/dbname
DB_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://root:biswa123@localhost:3306/meta_poc")
ECHO_SQL = os.getenv("SQL_ECHO", "false").lower() in ("1", "true", "yes")

engine = create_engine(
    DB_URL,
    echo=ECHO_SQL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
