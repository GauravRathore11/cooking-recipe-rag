import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
import os

load_dotenv()

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
EMBEDDING_MODEL  = os.getenv('EMBEDDING_MODEL')
COLLECTION_NAME = os.getenv('COLLECTION_NAME')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL')


def get_recipe_collection():
    db_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        url=OLLAMA_BASE_URL,
        model_name=EMBEDDING_MODEL,
    )

    collection = db_client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=ollama_ef
    )

    print(f"Connected to recipe database ({collection.count()} recipes loaded)")
    return collection


# ─── Clean Query ─────────────────────────────────────────────────────────────

def clean_query(query: str) -> str:
    import re

    stopwords = {
        "please", "can", "you", "suggest", "something",
        "give", "me", "i", "want", "to", "make",
        "recipe", "dish", "food", "bro", "hey",
        "with", "using", "how", "what", "should"
    }

    query = query.lower()
    query = re.sub(r"[^\w\s]", "", query)

    words = [word for word in query.split() if word not in stopwords]

    return " ".join(words)