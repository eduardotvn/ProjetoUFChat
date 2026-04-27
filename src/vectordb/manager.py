import os
import json
import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

class GoogleEmbeddings(EmbeddingFunction):
    """Custom embedding function using Google Generative AI."""
    def __call__(self, input: Documents) -> Embeddings:
        response = genai.embed_content(
            model="models/text-embedding-004",
            content=input,
            task_type="retrieval_document"
        )
        return response['embedding']

# Initialize ChromaDB client (persistent)
client = chromadb.PersistentClient(path="./UFChat/chroma_db")
embedding_function = GoogleEmbeddings()

# Map categories to collection names
CATEGORY_MAP = {
    "Dúvidas Gerais e Contatos": "duvidas_contatos",
    "Links de Documentos": "links_documentos",
    "Novidades ou Notícias": "novidades_noticias",
    "Cardápio do RU": "cardapio_ru"
}

def get_collection(category: str):
    """Gets or creates a collection for the given category."""
    collection_name = CATEGORY_MAP.get(category)
    if not collection_name:
        raise ValueError(f"Category '{category}' does not have a mapped vector database.")
    
    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"}
    )

def index_json_file(file_path: str, category: str):
    """
    Reads a JSON file and indexes its content into the specified category's vector database.
    Converts each key-value pair in a JSON object into a single string for embedding.
    """
    collection = get_collection(category)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = []
    metadatas = []
    ids = []
    
    # If it's a dictionary (key-value pairs), treat each pair as a document
    if isinstance(data, dict):
        for key, value in data.items():
            content = f"{key} {value}"
            doc_id = f"{os.path.basename(file_path)}_{key}"
            
            documents.append(content)
            metadatas.append({"source": file_path, "key": key})
            ids.append(doc_id)
            
    # If it's a list, process each item
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                # Concatenate all key-values in the dict into one string
                content = " ".join([f"{k} {v}" for k, v in item.items()])
                doc_id = str(item.get("id") or f"{os.path.basename(file_path)}_{i}")
            else:
                content = str(item)
                doc_id = f"{os.path.basename(file_path)}_{i}"
                
            documents.append(content)
            metadatas.append({"source": file_path})
            ids.append(doc_id)
    
    if documents:
        collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    return f"Indexed {len(documents)} items from {file_path} into {category}."

def search_vectors(query: str, category: str, n_results: int = 3):
    """
    Searches the vector database for the most similar items to the query.
    """
    collection = get_collection(category)
    
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    # Format results to return the 'documents' (contents)
    # results['documents'] is a list of lists (one list per query_text)
    if results['documents']:
        return results['documents'][0]
    return []
