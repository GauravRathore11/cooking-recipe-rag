import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
import os

# Build paths relative to this file's location so it works regardless of CWD
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(BASE_DIR, '.env'))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
EMBEDDING_MODEL  = os.getenv('EMBEDDING_MODEL')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL')


def get_recipe_collection():
    db_path = os.path.join(BASE_DIR, 'vector_db_recipe')
    db_client = chromadb.PersistentClient(path=db_path)

    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        url=OLLAMA_BASE_URL,
        model_name=EMBEDDING_MODEL,
    )

    collection = db_client.get_collection(
        name='recipes',
        embedding_function=ollama_ef
    )

    print(f"Connected to recipe database ({collection.count()} recipes loaded)")
    return collection




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