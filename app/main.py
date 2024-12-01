import re
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from langchain_text_splitters import CharacterTextSplitter
import spacy
from sqlalchemy.orm import Session
from translate import Translator
from app.crud.file_crud import create_file, file_exists
from app.db.db import SessionLocal, get_database_schema, get_db
from pathlib import Path
from pydantic import BaseModel
from app.crud.vector_store_crud import create_or_update_vector_store
from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from langdetect import detect
from langchain.agents import initialize_agent, Tool, AgentType
from langchain_openai import ChatOpenAI
import os
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI

app = FastAPI()  

load_dotenv()
router = APIRouter()
nlp = spacy.load("es_core_news_sm")
openai_api_key = os.getenv("OPENAI_API_KEY")

UPLOAD_FOLDER = './uploaded_files'
VECTOR_STORE_FOLDER = './vector_stores'
VECTOR_STORE_JSON = f'{VECTOR_STORE_FOLDER}/vector_store.json'

class QueryRequest(BaseModel):
    query: str
    k: int

class UserQueryRequest(BaseModel):
    query: str
    model: str 

def clean_text(raw_text):
    text = re.sub(r"metadata=\{.*?\}", "", raw_text)
    text = re.sub(r"http[s]?://\S+", "", text)
    text = re.sub(r"(?<![\.\?!])\n", " ", text) 
    text = re.sub(r"Ignoring.*?object.*?\n", "", text)
    text = re.sub(r"Special Issue.*?\n", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = text.strip()
    return text

def lemmatize_text(text):
    doc = nlp(text)
    lemmatized = " ".join([token.lemma_ for token in doc if not token.is_stop and not token.is_punct])
    return lemmatized

def process_pdf(file_path):
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    processed_texts = []
    for doc in documents:
        cleaned_text = clean_text(doc.page_content)
        lemmatized_text = lemmatize_text(cleaned_text)
        doc.page_content = lemmatized_text
        processed_texts.append(doc)
    
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return text_splitter.split_documents(processed_texts)

def create_vector_index(texts, existing_index=None):
    embeddings = OpenAIEmbeddings() 
    if existing_index:
        existing_index.add_documents(texts)
        return existing_index
    return FAISS.from_documents(texts, embeddings)

def create_tools(vector_store):
    retriever = vector_store.as_retriever()
    tool = Tool(
        name="Document Retriever",
        func=lambda query: retriever.invoke(query),  
        description="Usado para recuperar documentos relevantes para la consulta"
    )
    return [tool]

def create_agent(tools):
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=openai_api_key)
    agent = initialize_agent(
        tools,
        llm,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True  
    )
    return agent 

@app.post('/uploadfile/')
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    
    # Create the folder if it does not exist
    Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(VECTOR_STORE_FOLDER).mkdir(parents=True, exist_ok=True)

    #save the file to the file systema
    file_location = f"{UPLOAD_FOLDER}/{file.filename}"

    existing_file = file_exists(db, filename=file.filename, filepath=file_location)
    if existing_file:
        raise HTTPException(status_code=400, detail="El archivo ya existe en tu BD")

    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())
        
    db_file = create_file(db, filename=file.filename, filetype="pdf", filepath=file_location)
    
    texts = process_pdf(file_location)
    new_vector_store = create_vector_index(texts)

    if Path(VECTOR_STORE_JSON).is_file():
        existing_index = FAISS.load_local(VECTOR_STORE_FOLDER, OpenAIEmbeddings())
        existing_index.add_documents(new_vector_store.docstore._dict.values())
    else:
        existing_index = new_vector_store

    existing_index.save_local(VECTOR_STORE_FOLDER)

    create_or_update_vector_store(db, VECTOR_STORE_JSON)

    return {"filename": file.filename, "file_id": db_file.id}
 
@app.post('/ask/')
async def ask_question(request: UserQueryRequest, db: Session = Depends(get_db)):
    if not Path(f"{VECTOR_STORE_FOLDER}/index.faiss").is_file() or not Path(f"{VECTOR_STORE_FOLDER}/index.pkl").is_file():
        raise HTTPException(status_code=404, detail="Índice vectorial no encontrado. Por favor, sube un archivo primero.")
    
    try:
        embeddings = OpenAIEmbeddings()
        vector_store = FAISS.load_local(VECTOR_STORE_FOLDER, embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cargar el vector store: {str(e)}")

    tools = create_tools(vector_store)
    agent = create_agent(tools)

    try:
        response = agent.invoke(request.query)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar el agente: {str(e)}")

    return {"query": request.query, "response": response}

@app.get('/check-pdf-loaded/')
async def check_pdf_loaded():
    pdf_files = [f for f in Path(UPLOAD_FOLDER).iterdir() if f.suffix.lower() == '.pdf']

    if pdf_files:
        return {"pdf_loaded": True}
    else:
        return {"pdf_loaded": False}