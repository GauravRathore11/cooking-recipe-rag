"""
Flask API Server for the Cooking Recipe RAG application.
Serves the frontend and exposes API endpoints for chat and adding recipes.
"""

import os
import sys
import json

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from ollama import Client as OllamaClient

# Path Setup 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')

# Add backend dir to sys.path so we can import our modules
sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, '.env'))

#  Imports from our project 

from src._03_rag import search_recipes
from src._05_add_recipe import add_recipe
from utils.functions import get_recipe_collection, clean_query
from utils.prompts import SYSTEM_PROMPT, RECIPE_OUTPUT_FORMAT, RAG_QUERY_PROMPT

# Config 

OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL')
LLM_MODEL = os.getenv('LLM_MODEL')

# Flask App 

app = Flask(__name__)
CORS(app)

# Initialize the ChromaDB collection once at startup
print("Starting Recipe RAG server...")
collection = get_recipe_collection()


# Serve Frontend 

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# API: Chat (SSE Streaming) 

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_query = data.get('query', '').strip()

    if not user_query:
        return jsonify({"error": "Please enter a query."}), 400

    # 1. Clean the query
    cleaned = clean_query(user_query)

    # 2. Retrieve relevant recipes from ChromaDB
    context = search_recipes(collection, cleaned)

    if not context:
        return jsonify({"error": "No matching recipes found. Try different ingredients or dish name."}), 404

    # 3. Build the prompt
    full_user_prompt = RAG_QUERY_PROMPT.format(
        context=context,
        user_query=user_query
    )

    # 4. Stream response from Ollama via SSE
    def generate():
        client = OllamaClient(host=OLLAMA_BASE_URL)

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
            # Send each token as an SSE event
            yield f"data: {json.dumps({'token': token})}\n\n"

        # Signal the end of stream
        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


# API: Add Recipe 

@app.route('/api/recipe', methods=['POST'])
def add_recipe_endpoint():
    data = request.get_json()

    title = data.get('title', '').strip()
    ingredients = data.get('ingredients', '').strip()
    instructions = data.get('instructions', '').strip()

    if not title or not ingredients or not instructions:
        return jsonify({"error": "All fields (title, ingredients, instructions) are required."}), 400

    try:
        recipe_id = add_recipe(collection, title, ingredients, instructions)
        return jsonify({
            "message": f"Recipe '{title}' added successfully!",
            "recipe_id": recipe_id
        }), 201
    except Exception as e:
        return jsonify({"error": f"Failed to add recipe: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
