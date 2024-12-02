from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Q&A API with Model Integration")

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Bienvenido al endpoint de consultas con el modelo"}