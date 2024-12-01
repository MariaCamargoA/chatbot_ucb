import requests
from PyPDF2 import PdfReader
import unicodedata
import re
import time
import pdfplumber
from sentence_transformers import SentenceTransformer, util

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer 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"}

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Puedes cambiar el modelo si deseas mayor precisión

def query_huggingface_api_with_roles(system_message: str, user_message: str, retries=3, wait_time=10):
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.3",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 500,
        "stream": False
    }
    
    for _ in range(retries):
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 503:
            print(f"Modelo no disponible. Reintentando en {wait_time} segundos...")
            time.sleep(wait_time)
        else:
            raise Exception(f"Request failed: {response.status_code}, {response.text}")
    
    raise Exception("Modelo no disponible después de varios intentos")

def extract_text_from_pdfs(pdf_paths):
    text_data = []
    for path in pdf_paths:
        with pdfplumber.open(path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            text_data.append(text)
    return text_data

def split_text_into_chunks(text_data, chunk_size=500):
    chunks = []
    for text in text_data:
        text = normalize_text(text)
        sentences = re.split(r'(?<=\.)\s+', text)
        chunk = ""
        
        for sentence in sentences:
            if len(chunk + sentence) > chunk_size:
                chunks.append(chunk)
                chunk = sentence
            else:
                chunk += " " + sentence
                
        if chunk:
            chunks.append(chunk)
    
    return chunks

def normalize_text(text):
    text = re.sub(r'\x00', '', text)
    text = re.sub(r'\n+', ' ', text) 
    text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^a-zA-Z0-9\s.,;:¿?¡!]", "", text) 
    text = re.sub(r"\s+", " ", text).strip()

    return text.lower()

def get_response_from_model(query, relevant_chunks):
    system_message = """
    Eres un asistente de inteligencia artificial especializado en resumir y analizar texto. 
    Proporciona respuestas claras, precisas y en español basadas en el texto proporcionado.
    Limitate a responder UNICAMENTE la pregunta.
    """
    
    combined_chunks = "\n".join(relevant_chunks)
    user_message = f"Contexto: {combined_chunks}\n\nPregunta: {query}"
    response = query_huggingface_api_with_roles(system_message, user_message)
    
    choices = response.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    
    return "No se pudo obtener una respuesta del modelo."

def filter_relevant_chunks(query, chunks, top_k=1):
    query_embedding = embedding_model.encode(query, convert_to_tensor=True)
    chunk_embeddings = embedding_model.encode(chunks, convert_to_tensor=True)
    
    similarities = util.cos_sim(query_embedding, chunk_embeddings)[0]
    
    top_results = similarities.topk(k=top_k)
    relevant_chunks = [chunks[i] for i in top_results.indices]
    
    return relevant_chunks

def main():
    pdf_paths = [r"C:\Users\BELEN\Monsters university\10mo semestre\Taller de grado 1\Becas - Universidad Católica Boliviana San Pablo Sede Cochabamba.pdf", 
                 r"C:\Users\BELEN\Monsters university\10mo semestre\Taller de grado 1\Inscripciones_preucb.pdf",
                 r"C:\Users\BELEN\Monsters university\10mo semestre\Taller de grado 1\Oferta Inscripciones de invierno - Universidad Católica Boliviana San Pablo Sede Cochabamba.pdf"]
    text_data = extract_text_from_pdfs(pdf_paths)
    chunks = split_text_into_chunks(text_data)

    print("Ingrese su consulta. Escriba 'quit' o 'exit' para salir.")
    
    while True:
        query = input("Usuario: ")
        
        if query.lower() in {"quit", "exit"}:
            print("Saliendo del programa. ¡Hasta luego!")
            break

        relevant_chunks = filter_relevant_chunks(query, chunks, top_k=3)
        
        response = get_response_from_model(query, relevant_chunks)
        
        print(f"\nRespuesta del modelo:\n{response}\n")

if __name__ == "__main__":
    main()
