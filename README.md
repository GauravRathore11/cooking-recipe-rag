# Cooking Recipe RAG - AI-Powered Kitchen Assistant

## Project Overview

Cooking Recipe RAG is a full-stack web application that uses Retrieval-Augmented Generation (RAG) to help users discover recipes. Users can type in ingredients they have on hand or the name of a dish, and the system retrieves relevant recipes from a vector database, then passes them to a local LLM which generates a well-formatted, context-aware response.

The application also allows users to add their own recipes through the web interface. New recipes are stored in both the vector database and the source CSV file, making them immediately searchable.

### Key Features

- Semantic search over a recipe dataset using vector embeddings
- Streaming AI responses powered by a local LLM via Ollama
- Web-based chat interface for recipe queries
- Add Recipe form to contribute new recipes to the database
- Fully local and offline -- no cloud APIs required after initial model download
- Automated data cleaning pipeline

---

## Tools and Technologies

| Component | Tool | Purpose |
|-----------|------|---------|
| Backend Framework | Flask | REST API server, serves frontend, handles SSE streaming |
| CORS | Flask-CORS | Cross-origin request handling |
| LLM | Ollama (qwen2.5:1.5b) | Local language model for generating recipe responses |
| Embeddings | Ollama (nomic-embed-text) | Generates vector embeddings for semantic search |
| Vector Database | ChromaDB | Stores and retrieves recipe embeddings locally |
| Data Processing | Pandas | CSV loading, cleaning, and transformation |
| Environment Config | python-dotenv | Loads configuration from .env file |
| Frontend | HTML, CSS, JavaScript | Chat UI and Add Recipe form (vanilla, no framework) |
| Font | Inter (Google Fonts) | Typography for the web interface |

### Python Dependencies (requirements.txt)

```
pandas
chromadb
ollama
google-genai
python-dotenv
streamlit
flask
flask-cors
```

Note: `google-genai` and `streamlit` are listed in requirements.txt but are not actively used in the current version of the application. The core dependencies are pandas, chromadb, ollama, flask, flask-cors, and python-dotenv.

---

## Architecture Overview

```
                    +---------------------------+
                    |      User (Browser)       |
                    +---------------------------+
                               |
                    HTTP (GET / POST, SSE stream)
                               |
                    +---------------------------+
                    |   Flask Server (app.py)   |
                    |   - Serves frontend       |
                    |   - /api/chat  (POST)     |
                    |   - /api/recipe (POST)    |
                    +---------------------------+
                         |             |
             +-----------+             +-----------+
             |                                     |
    +------------------+                 +-------------------+
    |  RAG Pipeline    |                 |  Add Recipe       |
    |  (_03_rag.py)    |                 |  (_05_add_recipe) |
    +------------------+                 +-------------------+
             |                                     |
    +------------------+                           |
    |  Query Cleaning  |                           |
    |  (functions.py)  |                           |
    +------------------+                           |
             |                                     |
    +--------------------------------------------------+
    |              ChromaDB (vector_db_recipe/)         |
    |              Embedding: nomic-embed-text          |
    +--------------------------------------------------+
             |
    +------------------+
    |  Ollama LLM      |
    |  qwen2.5:1.5b    |
    |  (localhost:11434)|
    +------------------+
             |
      Streamed response
      back to browser
```

### How the RAG Pipeline Works

1. The user types a query (ingredients or dish name) in the chat interface.
2. The frontend sends a POST request to `/api/chat` with the query.
3. The backend cleans the query by removing stopwords and punctuation.
4. The cleaned query is used to perform a semantic search against ChromaDB, retrieving the top 5 most similar recipes.
5. The retrieved recipes are injected into a prompt template along with the original user query.
6. The prompt is sent to the Ollama LLM (qwen2.5:1.5b), which generates a formatted recipe response.
7. The response is streamed back to the browser token-by-token using Server-Sent Events (SSE).

---

## Project Structure

```
cooking-recipe-rag/
|
|-- README.md
|-- README.docx
|-- requirements.txt
|-- .gitignore
|
|-- backend/
|   |-- app.py                          # Flask server (entry point)
|   |-- .env                            # Environment variables (not committed)
|   |
|   |-- src/
|   |   |-- _01_data_prep.py            # Cleans raw CSV data
|   |   |-- _02_vector_db.py            # Embeds recipes into ChromaDB
|   |   |-- _03_rag.py                  # Semantic search over ChromaDB
|   |   |-- _04_ask_ai.py               # CLI-based recipe assistant
|   |   |-- _05_add_recipe.py           # Adds recipes to DB and CSV
|   |
|   |-- utils/
|   |   |-- functions.py                # Shared helpers (DB connection, query cleaning)
|   |   |-- prompts.py                  # LLM prompt templates
|   |
|   |-- dataset/
|   |   |-- _01_raw/
|   |   |   |-- recipes.csv             # Original raw recipe data
|   |   |-- _02_cleaned/
|   |       |-- recipes_cleaned.csv     # Cleaned and processed recipes
|   |
|   |-- vector_db_recipe/               # ChromaDB persistent storage
|
|-- frontend/
    |-- index.html                      # Main HTML page
    |-- style.css                       # Styling (black/white/grey palette)
    |-- script.js                       # Chat logic, SSE streaming, add recipe
```

---

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- Ollama installed and available on your system
- The following Ollama models downloaded:
  - `qwen2.5:1.5b` (language model)
  - `nomic-embed-text` (embedding model)

### Step 1: Clone the repository

```bash
git clone <repository-url>
cd cooking-recipe-rag
```

### Step 2: Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Start Ollama

Open a separate terminal and start the Ollama server:

```bash
ollama serve
```

If you haven't downloaded the required models yet:

```bash
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
```

### Step 4: Prepare the dataset (one-time)

Place your raw recipes CSV file at `backend/dataset/_01_raw/recipes.csv`, then run:

```bash
cd backend/src
python _01_data_prep.py
```

This reads the raw CSV, renames columns (TranslatedRecipeName -> title, TranslatedIngredients -> ingredients, TranslatedInstructions -> directions), drops rows with missing values, and saves the cleaned output to `backend/dataset/_02_cleaned/recipes_cleaned.csv`.

### Step 5: Build the vector database (one-time)

```bash
cd backend/src
python _02_vector_db.py
```

This reads the cleaned CSV, combines each recipe's title and ingredients into a single document string, and inserts them into ChromaDB in batches of 100. ChromaDB automatically generates embeddings using the nomic-embed-text model via Ollama. The database is stored locally at `backend/vector_db_recipe/`.

### Step 6: Start the application

```bash
cd backend
python app.py
```

Open your browser and go to `http://localhost:5000`. You will see the chat interface.

---

## Usage

### Chat (Recipe Search)

1. Open `http://localhost:5000` in your browser.
2. Click the "Chat" tab in the sidebar (selected by default).
3. Type your query in the input field. Examples:
   - "I have tomatoes and basil"
   - "how to make biryani"
   - "chicken with yogurt"
4. Press Enter or click the send button.
5. The AI will stream a formatted recipe response in real time.

### Add a Recipe

1. Click the "Add Recipe" tab in the sidebar.
2. Fill in the recipe title, ingredients, and instructions.
3. Click "Add Recipe".
4. The recipe is saved to both ChromaDB and the CSV file, and becomes immediately searchable in the chat.

### CLI Mode (Alternative)

You can also use the recipe assistant from the command line without starting the web server:

```bash
cd backend/src
python _04_ask_ai.py
```

Type your queries at the prompt. Type `quit`, `exit`, or `q` to stop.

---

## Detailed Code Walkthrough

### _01_data_prep.py

Reads the raw recipe CSV, renames three columns to standardized names (title, ingredients, directions), drops rows where any of these fields are missing, and writes the result to a cleaned CSV file.

### _02_vector_db.py

Connects to a local ChromaDB instance with persistent storage. Creates an Ollama embedding function pointing to localhost:11434 using the nomic-embed-text model. Deletes any existing "recipes" collection to avoid conflicts, then creates a fresh one. For each recipe, combines title and ingredients into a single document and stores the full metadata (title, ingredients, instructions). Processes in batches of 100 to manage memory.

### _03_rag.py

Contains the `search_recipes` function. Takes a ChromaDB collection and a query string, performs a semantic similarity search, and returns the top K results formatted as a context string. Each result includes the recipe title, ingredients, and instructions.

### _04_ask_ai.py

A standalone CLI application. Connects to ChromaDB on startup, then enters a loop where it accepts user input, cleans the query, searches for matching recipes, builds a RAG prompt, and streams the LLM response to the terminal.

### _05_add_recipe.py

Handles adding new recipes. The `add_recipe` function writes the recipe to both ChromaDB (so it becomes searchable immediately) and appends it to the cleaned CSV file (so it persists across database rebuilds). Each recipe gets a unique ID based on the current timestamp.

### app.py (Flask server)

The main entry point for the web application. Serves the frontend static files and exposes two API endpoints:

- `POST /api/chat` -- Accepts a query, runs it through the RAG pipeline, and streams the LLM response back as Server-Sent Events.
- `POST /api/recipe` -- Accepts title, ingredients, and instructions, adds the recipe to both ChromaDB and the CSV file.

### utils/functions.py

Contains shared utility functions:
- `get_recipe_collection()` -- Connects to the existing ChromaDB collection with the Ollama embedding function.
- `clean_query()` -- Lowercases the input, removes punctuation, and filters out common stopwords to improve search quality.

### utils/prompts.py

Stores all LLM prompt templates:
- `SYSTEM_PROMPT` -- Instructs the LLM to act as a chef, only use provided context, and avoid hallucination.
- `RECIPE_OUTPUT_FORMAT` -- Defines the structured output format (title, description, ingredients, instructions, tips).
- `RAG_QUERY_PROMPT` -- Template that injects the retrieved recipe context and the user query.

### Frontend (index.html, style.css, script.js)

A single-page application with two views controlled by sidebar navigation:
- Chat view: Displays a conversation-style interface. Messages are streamed from the backend using the Fetch API's ReadableStream to parse SSE data in real time.
- Add Recipe view: A form that submits recipe data to the backend API.

The design uses a black and white color scheme with the Inter font. The layout is responsive -- the sidebar collapses on smaller screens.

---

## Environment Variables

The backend reads configuration from `backend/.env`:

```
TOP_K_RESULTS = 5
EMBEDDING_MODEL = nomic-embed-text
OLLAMA_BASE_URL = http://localhost:11434
LLM_MODEL = qwen2.5:1.5b
```

| Variable | Description | Default |
|----------|-------------|---------|
| TOP_K_RESULTS | Number of recipes retrieved per search | 5 |
| EMBEDDING_MODEL | Ollama model used for embeddings | nomic-embed-text |
| OLLAMA_BASE_URL | URL where Ollama is running | http://localhost:11434 |
| LLM_MODEL | Ollama model used for text generation | qwen2.5:1.5b |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection refused" when starting the app | Make sure Ollama is running: `ollama serve` |
| "Model not found" error | Download the required models: `ollama pull qwen2.5:1.5b` and `ollama pull nomic-embed-text` |
| Vector database not found | Run `python _02_vector_db.py` from the `backend/src/` directory first |
| No matching recipes returned | Try simpler keywords. The query cleaner removes common words like "please", "can", "recipe", etc. |
| Slow responses | The LLM runs locally on your hardware. A smaller model or fewer TOP_K_RESULTS may help |
| Frontend not loading | Make sure you started the server with `python app.py` from the `backend/` directory and are visiting `http://localhost:5000` |

---

## Privacy

Everything runs locally on your machine. Ollama handles all LLM inference on your CPU or GPU. ChromaDB stores all embeddings on disk. No data is sent to any external server. Once the models are downloaded, no internet connection is needed.

---

## License

This project was created as an academic/personal project. Add your license here if applicable.
