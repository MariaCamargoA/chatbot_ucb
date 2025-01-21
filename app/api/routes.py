import os
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.core.config import UPLOAD_FOLDER, VECTOR_STORE_FOLDER, VECTOR_STORE_JSON
from app.db.db import create_file, create_or_update_vector_store, file_exists, get_db
from pathlib import Path
from app.models.user_query_request import UserQueryRequest
from app.services.model import query_huggingface_api_with_roles
from app.services.pdf_processing import process_pdf
from app.services.embedding import combine_vector_stores, create_vector_index, filter_relevant_chunks, load_vector_store, save_vector_store

router = APIRouter()

@router.post('/uploadfile/')
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(VECTOR_STORE_FOLDER).mkdir(parents=True, exist_ok=True)

    file_location = f"{UPLOAD_FOLDER}/{file.filename}"

    existing_file = file_exists(db, filename=file.filename, filepath=file_location)
    if existing_file:
        raise HTTPException(status_code=400, detail="El archivo ya existe en tu BD")

    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())

    db_file = create_file(db, filename=file.filename, filetype="pdf", filepath=file_location)

    texts = process_pdf(file_location)
    filename_without_extension = os.path.splitext(file.filename)[0]
    new_vector_store = create_vector_index(texts, filename_without_extension)

    if Path(VECTOR_STORE_JSON).is_file():
        existing_vector_store = load_vector_store(VECTOR_STORE_JSON)
        combined_vector_store = combine_vector_stores(existing_vector_store, new_vector_store)
    else:
        combined_vector_store = new_vector_store

    save_vector_store(combined_vector_store, VECTOR_STORE_JSON)

    create_or_update_vector_store(db, VECTOR_STORE_JSON)

    return {"filename": file.filename, "file_id": db_file.id}
    
@router.post('/ask/')
async def ask_question(request: UserQueryRequest, db: Session = Depends(get_db)):
    if not Path(f"{VECTOR_STORE_FOLDER}/vector_store.json").is_file():
        raise HTTPException(status_code=404, detail="Índice vectorial no encontrado. Por favor, sube un archivo primero.")
    
    vector_store = load_vector_store(VECTOR_STORE_JSON)

    try:
        relevant_chunks = filter_relevant_chunks(request.query, vector_store, top_k=7)
        print(relevant_chunks)
        system_message = """
        Eres un asistente virtual especializado en apoyar a estudiantes, docentes y personal administrativo de la Universidad Católica Boliviana, sede Cochabamba.
        Tu objetivo principal es proporcionar respuestas claras, precisas y en español, basándote exclusivamente en el contexto y la información proporcionados.
        Sigue las siguientes reglas:
        1. Limita tus respuestas ÚNICAMENTE a la información contenida en el contexto proporcionado. Evita cualquier tipo de información no relacionada con la Universidad Católica Boliviana, sede Cochabamba.
        2. Evita generar información especulativa, enlaces inválidos o contenido irrelevante.        
        3. Si no se te envía un contexto, responde únicamente: "No puedo darte una respuesta, ya que no tengo información al respecto."        
        """
        combined_chunks = "\n".join([chunk['text'] for chunk in relevant_chunks])
        user_message = f"Context: {combined_chunks}\n\nQuestion: {request.query}"
        
        response = query_huggingface_api_with_roles(system_message, user_message)

        choices = response.get("choices", [])
        if choices:
            model_response = choices[0].get("message", {}).get("content", "")
        else:
            model_response = "Could not get a response from the model."
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar la consulta: {str(e)}")

    return {"query": request.query, "response": model_response}