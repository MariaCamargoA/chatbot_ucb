import re
import unicodedata
import pdfplumber

def normalize_text(text):
    text = re.sub(r'\x00', '', text)
    text = re.sub(r'\n+', ' ', text) 
    text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^a-zA-Z0-9\s.,;:¿?¡!]", "", text) 
    text = re.sub(r"\s+", " ", text).strip()

    return text.lower()

def split_text_into_chunks(text, chunk_size=500):
    chunks = []
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

def process_pdf(file_path: str, chunk_size: int = 500) -> list:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or "" 

    text = normalize_text(text)
    print("Texto limpio:", text) 

    chunks = split_text_into_chunks(text, chunk_size=chunk_size)
    
    return chunks