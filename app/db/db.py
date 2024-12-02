from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from app.models.file import File
from app.models.vector_store import VectorStore
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_file(db: Session, filename: str, filetype: str, filepath: str):
    db_file = File(filename=filename, filetype=filetype, filepath=filepath)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file    

def file_exists(db: Session, filename: str, filepath: str):
    return db.query(File).filter((File.filename == filename) | (File.filepath == filepath)).first()

def create_vector_store(db: Session, filepath: str):
    db_store = VectorStore(filepath=filepath)
    db.add(db_store)
    db.commit()
    db.refresh(db_store)
    return db_store

def get_vector_store(db: Session):
    return db.query(VectorStore).first()

def create_or_update_vector_store(db: Session, filepath: str):
    existing_store = get_vector_store(db)

    if existing_store:
        existing_store.filepath = filepath
        db.commit()
        return existing_store
    else:
        return create_vector_store(db, filepath)