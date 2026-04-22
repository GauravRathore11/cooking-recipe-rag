"""
_03_ask_ai.py — The RAG-powered recipe assistant.

Flow:
  1. Connects to the existing ChromaDB vector database (built by _02_vector_db.py)
  2. Takes user input: raw ingredients OR a dish name
  3. Queries ChromaDB for the most relevant recipes (semantic search)
  4. Sends the retrieved context + user query to Ollama LLM
  5. Streams a beautifully formatted recipe back to the terminal
"""

import sys
import io

# Fix Windows terminal encoding so emojis don't crash the script
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")

import chromadb
from chromadb.utils import embedding_functions
from ollama import Client as OllamaClient

from prompts import SYSTEM_PROMPT, RECIPE_OUTPUT_FORMAT, RAG_QUERY_PROMPT


# ─── Configuration ───────────────────────────────────────────────────────────

OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3"              # Change to "qwen2.5" if you prefer
CHROMA_DB_PATH = "./recipe_db"
COLLECTION_NAME = "recipes"
TOP_K_RESULTS = 5                  # Number of recipes to retrieve from vector DB


# ─── Vector DB Connection ────────────────────────────────────────────────────

def get_recipe_collection():
    """Connect to the existing ChromaDB and return the recipes collection."""
    db_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        url=OLLAMA_BASE_URL,
        model_name=EMBEDDING_MODEL,
    )

    collection = db_client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=ollama_ef
    )

    print(f"✅ Connected to recipe database ({collection.count()} recipes loaded)")
    return collection


# ─── RAG: Retrieve Relevant Recipes ──────────────────────────────────────────

def search_recipes(collection, query: str, n_results: int = TOP_K_RESULTS):
    """
    Perform a semantic search against the vector DB.
    Returns the top matching recipes as a formatted context string.
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    if not results or not results["metadatas"] or not results["metadatas"][0]:
        return None

    # Build a clean context string from the retrieved recipes
    context_parts = []
    for i, metadata in enumerate(results["metadatas"][0], start=1):
        title = metadata.get("title", "Unknown")
        ingredients = metadata.get("ingredients", "N/A")
        instructions = metadata.get("instructions", "N/A")

        context_parts.append(
            f"Recipe {i}: {title}\n"
            f"  Ingredients: {ingredients}\n"
            f"  Instructions: {instructions}\n"
        )

    return "\n".join(context_parts)


# ─── LLM: Generate Response ──────────────────────────────────────────────────

def ask_llm(user_query: str, context: str):
    """
    Send the RAG context + user query to Ollama and stream the response.
    """
    client = OllamaClient(host=OLLAMA_BASE_URL)

    # Build the full prompt from our templates
    full_user_prompt = RAG_QUERY_PROMPT.format(
        context=context,
        user_query=user_query
    )

    print("\n🤖 Chef Bot is cooking up a response...\n")
    print("─" * 60)

    # Stream the response for a nice real-time effect
    full_response = ""
    stream = client.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + RECIPE_OUTPUT_FORMAT},
            {"role": "user", "content": full_user_prompt},
        ],
        stream=True,
    )

    for chunk in stream:
        token = chunk["message"]["content"]
        print(token, end="", flush=True)
        full_response += token

    print("\n" + "─" * 60)
    return full_response


# ─── Main Interactive Loop ───────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  🍳  RECIPE BOT — Your AI-Powered Kitchen Assistant")
    print("=" * 60)
    print("\nTell me what ingredients you have, or ask for a dish by name.")
    print("Type 'quit' or 'exit' to leave.\n")

    # Connect to vector DB once
    collection = get_recipe_collection()

    while True:
        print()
        user_input = input("🧑‍🍳 You: ").strip()

        if not user_input:
            print("Please enter some ingredients or a dish name!")
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("\n👋 Happy cooking! Bon appétit!")
            break

        # Step 1: Retrieve relevant recipes from vector DB
        context = search_recipes(collection, user_input)

        if not context:
            print("😕 Sorry, I couldn't find any matching recipes in the database.")
            continue

        # Step 2: Send to LLM with the retrieved context
        ask_llm(user_input, context)


if __name__ == "__main__":
    main()
