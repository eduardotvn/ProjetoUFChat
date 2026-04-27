import os
import json
import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

client_genai = genai.Client(api_key=GEMINI_API_KEY)

class GoogleEmbeddings(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        model_id = "models/gemini-embedding-2"
        
        embeddings = []
        for text in input:
            response = client_genai.models.embed_content(
                model=model_id,
                contents=text
            )
            embeddings.append(list(map(float, response.embeddings[0].values)))
            
        return embeddings

client = chromadb.PersistentClient(path="./UFChatDB/chroma_db")
embedding_function = GoogleEmbeddings()

CATEGORY_MAP = {
    "Dúvidas Gerais e Contatos": "duvidas_contatos",
    "Links de Documentos": "links_documentos",
    "Novidades ou Notícias": "novidades_noticias",
    "Cardápio do RU": "cardapio_ru"
}

def get_collection(category: str):

    collection_name = CATEGORY_MAP.get(category)
    if not collection_name:
        raise ValueError(f"Category '{category}' does not have a mapped vector database.")
    
    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"}
    )

def index_json_file(file_path: str, category: str):

    collection = get_collection(category)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    documents = []
    metadatas = []
    ids = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            content = f"{key} {value}"
            doc_id = f"{os.path.basename(file_path)}_{key}"
            
            documents.append(content)
            metadatas.append({"source": file_path, "key": key})
            ids.append(doc_id)
            
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):

                content = " ".join([f"{k} {v}" for k, v in item.items()])
                doc_id = str(item.get("id") or f"{os.path.basename(file_path)}_{i}")
            else:
                content = str(item)
                doc_id = f"{os.path.basename(file_path)}_{i}"
                
            documents.append(content)
            metadatas.append({"source": file_path})
            ids.append(doc_id)
    
    if documents:
            print(f"Docs: {len(documents)}, IDs: {len(ids)}, Metas: {len(metadatas)}")
            
            if not (len(documents) == len(ids) == len(metadatas)):
                raise ValueError("Erro de consistência: as listas de documentos, IDs e metadatas têm tamanhos diferentes!")

            collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

    return f"Indexed {len(documents)} items from {file_path} into {category}."

def search_vectors(query: str, category: str, n_results: int = 3):

    collection = get_collection(category)
    
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    if results['documents']:
        return results['documents'][0]
    return []
