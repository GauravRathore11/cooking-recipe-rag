"""
Add Recipe Module
Handles adding user-submitted recipes to both ChromaDB and the cleaned CSV file.
"""

import os
import time
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, 'dataset', '_02_cleaned', 'recipes_cleaned.csv')


def add_recipe_to_db(collection, title: str, ingredients: str, instructions: str):
    """Add a single recipe to the ChromaDB collection."""
    
    recipe_id = f"user_recipe_{int(time.time() * 1000)}"
    
    document = f"{title} {ingredients}"
    
    metadata = {
        "title": title,
        "ingredients": ingredients,
        "instructions": instructions,
    }
    
    collection.add(
        ids=[recipe_id],
        documents=[document],
        metadatas=[metadata],
    )
    
    print(f"Added recipe '{title}' to ChromaDB (ID: {recipe_id})")
    return recipe_id


def add_recipe_to_csv(title: str, ingredients: str, instructions: str):
    """Append a recipe row to the cleaned CSV file."""
    
    new_row = pd.DataFrame([{
        "title": title,
        "ingredients": ingredients,
        "directions": instructions,
    }])
    
    if os.path.exists(CSV_PATH):
        new_row.to_csv(CSV_PATH, mode='a', header=False, index=False)
    else:
        new_row.to_csv(CSV_PATH, index=False)
    
    print(f"Appended recipe '{title}' to CSV")


def add_recipe(collection, title: str, ingredients: str, instructions: str):
    """Add a recipe to both ChromaDB and the CSV file."""
    
    recipe_id = add_recipe_to_db(collection, title, ingredients, instructions)
    add_recipe_to_csv(title, ingredients, instructions)
    
    return recipe_id
