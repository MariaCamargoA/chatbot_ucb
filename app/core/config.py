from pydantic_settings import BaseSettings

UPLOAD_FOLDER = "uploaded_files"
VECTOR_STORE_FOLDER = "vector_store"
VECTOR_STORE_JSON = f"{VECTOR_STORE_FOLDER}/vector_store.json"

class Settings(BaseSettings):
    API_URL: str
    API_KEY: str
    DATABASE_URL: str

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()