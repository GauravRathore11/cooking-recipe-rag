import pandas as pd
import chromadb
import os

from chromadb.utils import embedding_functions 

# Build paths relative to this file's location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def create_and_populate_db(df):
    print("Initializing local Chroma Vector DB with Ollama...")
    db_path = os.path.join(BASE_DIR, 'vector_db_recipe')
    db_client = chromadb.PersistentClient(path=db_path)
    
    # 1. Point Chroma directly to your local Ollama instance
    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        url="http://localhost:11434",
        model_name="nomic-embed-text",
    )
    
    # 2. Delete any existing collection to avoid embedding function conflicts
    existing_collections = [c.name for c in db_client.list_collections()]
    if "recipes" in existing_collections:
        print("Wiping old collection for fresh run...")
        db_client.delete_collection(name="recipes")
    
    # 3. Create a fresh collection with the Ollama embedding function
    collection = db_client.create_collection(
        name="recipes",
        embedding_function=ollama_ef
    )

    print(f"Sending {len(df)} recipes to Ollama for embedding. This is running locally!")
    
    ids = []
    documents = []
    metadatas = []

    # 3. We no longer generate embeddings manually here!
    # We just pack the data into lists.
    for index, row in df.iterrows():
        ids.append(f"recipe_{index}")
        documents.append(str(row['title']) + " " + str(row['ingredients']))  
        metadatas.append({                         
            "title": str(row['title']),
            "ingredients": str(row['ingredients']),
            "instructions": str(row['directions']) 
        })

    # 4. Add to database. Chroma will automatically pass the 'documents' 
    # to Ollama, get the vectors back, and save everything together!
    print("Processing and inserting data into Vector DB...")
    
    # We add them in batches of 100 to prevent overloading your local RAM
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        print(f"Adding batch {i} to {i + batch_size}...")
        collection.add(
            ids=ids[i:i + batch_size],
            documents=documents[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size]
        )
    
    print(f"Success! {collection.count()} recipes locally stored in Vector Database.")
    return collection

if __name__ == "__main__":
    # Ensure Ollama is running in the background before executing this!
    csv_path = os.path.join(BASE_DIR, 'dataset', '_02_cleaned', 'recipes_cleaned.csv')
    recipe_df = pd.read_csv(csv_path)
    db_collection = create_and_populate_db(recipe_df)