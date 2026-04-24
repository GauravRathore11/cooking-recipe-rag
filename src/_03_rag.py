import os
from dotenv import load_dotenv

load_dotenv()

TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS'))

# ─── RAG: Retrieve Relevant Recipes ──────────────────────────────────────────

def search_recipes(collection, query: str, n_results: int = TOP_K_RESULTS):
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    if not results or not results["metadatas"] or not results["metadatas"][0]:
        return None

    context_parts = []
    for i, metadata in enumerate(results["metadatas"][0], start=1):
        title = metadata.get("title", "Unknown")
        ingredients = metadata.get("ingredients", "N/A")
        instructions = metadata.get("instructions", "N/A")

        context_parts.append(
            f"Recipe {i}: {title}\n"
            f"Ingredients: {ingredients}\n"
            f"Instructions: {instructions}\n"
        )

    return "\n".join(context_parts)