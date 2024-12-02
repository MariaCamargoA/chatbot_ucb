import json
from sentence_transformers import SentenceTransformer, util
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

embedding_model = SentenceTransformer('all-MiniLM-L6-v2') 

def create_vector_index(texts, pdf_name):
    embeddings = embedding_model.encode(texts, convert_to_tensor=False).tolist()
    vector_store = [{"text": text, "embedding": embedding, "pdf_name": pdf_name} for text, embedding in zip(texts, embeddings)]
    return vector_store

def load_vector_store(file_path):
    with open(file_path, "r") as f:
        vector_store = json.load(f)
    return vector_store

def combine_vector_stores(existing_store, new_store):
    combined_store = existing_store + new_store
    return combined_store

def save_vector_store(vector_store, file_path):
    with open(file_path, "w") as f:
        json.dump(vector_store, f)

def filter_relevant_chunks(query, chunks, top_k=4):
    query_embedding = embedding_model.encode(query, convert_to_tensor=True)

    chunk_embeddings = [chunk["embedding"] for chunk in chunks]
    chunk_texts = [chunk["text"] for chunk in chunks]
    chunk_filenames = [chunk["pdf_name"] for chunk in chunks]

    similarities = util.cos_sim(query_embedding, chunk_embeddings)[0]
    top_results = similarities.topk(k=top_k)

    selected_filenames = [chunk_filenames[i] for i in top_results.indices]
    selected_chunks = [{"text": chunk_texts[i], "filename": chunk_filenames[i]} for i in top_results.indices]

    if len(set(selected_filenames)) > 1:
        title_similarities = []
        for filename in selected_filenames:
            title_similarity = util.cos_sim(query_embedding, embedding_model.encode(filename, convert_to_tensor=True))[0][0]
            title_similarities.append(title_similarity)

        best_title_idx = title_similarities.index(max(title_similarities))
        best_filename = selected_filenames[best_title_idx]

        best_chunks = [chunk for chunk in selected_chunks if chunk["filename"] == best_filename]

        return best_chunks
    else:
        return selected_chunks
