# 🍳 Cooking Recipe RAG - AI-Powered Kitchen Assistant

## 📋 Project Overview

**Cooking Recipe RAG** is an intelligent recipe recommendation system that uses **Retrieval-Augmented Generation (RAG)** to help users find recipes based on ingredients they have or dishes they want to cook. The system combines a vector database for semantic search with a local AI model to provide personalized, context-aware recipe suggestions with detailed instructions.

### Key Features
- 🔍 **Semantic Search**: Finds recipes similar to user queries using embeddings
- 🤖 **AI-Powered Responses**: Uses local LLM to generate formatted, personalized recipe suggestions
- 💾 **Vector Database**: Stores recipe embeddings for fast similarity-based retrieval
- 🏠 **Local & Privacy-First**: All processing happens locally (Ollama + ChromaDB)
- 📝 **Clean Data Pipeline**: Automated data preparation and cleaning workflow
- 🎯 **Interactive CLI**: User-friendly command-line interface for recipe queries

---

## 🛠️ Tools & Technologies Used

| Component | Tool | Purpose |
|-----------|------|---------|
| **LLM** | [Ollama](https://ollama.ai/) | Local language model for recipe generation (qwen2.5:1.5b) |
| **Embeddings** | Ollama (nomic-embed-text) | Semantic embeddings for recipe similarity search |
| **Vector Database** | [ChromaDB](https://www.trychroma.com/) | Stores and retrieves recipe embeddings |
| **Data Processing** | [Pandas](https://pandas.pydata.org/) | Data cleaning and transformation |
| **LLM Client** | [ollama-py](https://github.com/ollama/ollama-python) | Python client for Ollama |
| **Environment** | [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment variable management |
| **UI Framework** | [Streamlit](https://streamlit.io/) | (Optional) Web-based interface for the bot |
| **Google AI** | [google-genai](https://github.com/google/generative-ai-python) | (Optional) Integration with Google GenAI |

### Dependencies
```
pandas              - Data manipulation and analysis
chromadb            - Vector database for embeddings
ollama              - Local LLM and embeddings
google-genai        - Google AI integration (optional)
python-dotenv       - Environment configuration
streamlit           - Web UI framework (optional)
```

---

## 🔄 Project Flow & Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERACTION                         │
│              (CLI: _03_ask_ai.py)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    User Query Input
                           │
        ┌──────────────────┴──────────────────┐
        │   Query Cleaning (Remove Stopwords) │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │  SEMANTIC SEARCH (ChromaDB)         │
        │  Embedding: nomic-embed-text        │
        │  (Similarity Search)                │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │  RETRIEVE TOP-K RECIPES             │
        │  (Default: Top 5 matches)           │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │  LLM GENERATION (Ollama)            │
        │  Model: qwen2.5:1.5b                │
        │  Input: Context + User Query        │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │  STREAM FORMATTED RESPONSE          │
        │  (Real-time output to terminal)     │
        └──────────────────┬──────────────────┘
                           │
                    Formatted Recipe
                    with Instructions
```

### Detailed Workflow Stages

#### **Stage 1: Data Preparation** (`_01_data_prep.ipynb`)
- **Input**: Raw recipes CSV from `dataset/_01_raw/recipes.csv`
- **Process**:
  1. Load raw recipe data using Pandas
  2. Rename columns: `TranslatedRecipeName` → `title`, `TranslatedIngredients` → `ingredients`, `TranslatedInstructions` → `directions`
  3. Select relevant columns
  4. Remove rows with null/missing values
- **Output**: Cleaned CSV saved to `dataset/_02_cleaned/recipes_cleaned.csv`

#### **Stage 2: Vector Database Population** (`_02_vector_db.py`)
- **Input**: Cleaned recipes CSV
- **Process**:
  1. Initialize ChromaDB persistent client pointing to `vector_db_recipe/`
  2. Create Ollama embedding function (connects to localhost:11434)
  3. Delete existing "recipes" collection to avoid conflicts
  4. Create fresh collection with Ollama embedding function
  5. Combine title + ingredients into document text
  6. Add documents and metadata (title, ingredients, instructions) to collection
  7. Process in batches of 100 to prevent RAM overload
- **Output**: Vector database with embedded recipes stored locally in `vector_db_recipe/`

#### **Stage 3: Interactive Recipe Assistant** (`_03_ask_ai.py`)
1. **Connection Phase**:
   - Connect to existing ChromaDB collection
   - Verify Ollama is running on localhost:11434
   
2. **Query Processing**:
   - Accept user input (ingredients or dish name)
   - Clean query: lowercase, remove punctuation, filter stopwords
   
3. **Retrieval Phase**:
   - Use cleaned query as embedding input
   - Perform semantic search in ChromaDB
   - Retrieve top 5 most similar recipes with their metadata
   
4. **Generation Phase**:
   - Build RAG prompt with:
     - Retrieved recipe context
     - User's original query
     - System prompt with chef personality
   - Send to Ollama LLM (qwen2.5:1.5b)
   
5. **Response Phase**:
   - Stream response token-by-token for real-time feedback
   - Format using predefined output template with emojis
   - Display to user

#### **Key Processing Components**:

**Query Cleaning** (`clean_query` function):
- Removes common stopwords (please, can, you, want, etc.)
- Converts to lowercase
- Removes punctuation
- Returns refined query for better semantic matching

**Search Function** (`search_recipes`):
- Queries ChromaDB with semantic similarity
- Retrieves top K results (default: 5)
- Formats results into readable context string
- Includes title, ingredients, and instructions

**LLM Interaction** (`ask_llm`):
- Streams response from Ollama for real-time output
- Uses system prompts to control chef personality
- Enforces output format with structured template
- Prevents hallucination by limiting responses to provided context

---

## 📁 Project Structure

```
cooking-recipe-rag/
│
├── README.md                           # Project documentation
├── requirements.txt                    # Python dependencies
├── .gitignore                         # Git ignore rules
│
├── dataset/
│   ├── _01_raw/
│   │   └── recipes.csv               # Original raw recipe data
│   │
│   └── _02_cleaned/
│       └── recipes_cleaned.csv       # Cleaned & processed recipes
│
├── src/
│   ├── _01_data_prep.ipynb          # Data cleaning & preparation
│   ├── _02_vector_db.py             # Vector DB creation & population
│   └── _03_ask_ai.py                # Interactive recipe assistant (main)
│
├── utils/
│   └── prompts.py                   # LLM prompt templates
│
└── vector_db_recipe/                # ChromaDB storage
    ├── chroma.sqlite3               # Vector database
    └── [collection-uuids]/          # Embedded recipe collections
```

---

## 🚀 How to Use

### Prerequisites
- Python 3.8+
- Ollama running locally on `localhost:11434`
- Downloaded models: `qwen2.5:1.5b` and `nomic-embed-text`

### Installation

1. **Clone/setup the project**:
```bash
cd cooking-recipe-rag
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Start Ollama** (in another terminal):
```bash
ollama serve
# Download models if needed:
# ollama pull qwen2.5:1.5b
# ollama pull nomic-embed-text
```

### Running the Pipeline

#### Step 1: Prepare Data (One-time)
```bash
cd src
jupyter notebook _01_data_prep.ipynb
# Run all cells to clean the recipe data
```

#### Step 2: Build Vector Database (One-time)
```bash
cd src
python _02_vector_db.py
# This will create/populate the local vector database
```

#### Step 3: Start the Recipe Assistant
```bash
cd src
python _03_ask_ai.py
```

#### Example Interactions
```
🧑‍🍳 You: tomatoes and basil
🤖 Chef Bot is cooking up a response...
🍽️ **Recipe: Fresh Tomato Pasta**
...

🧑‍🍳 You: how to make biryani
🤖 Chef Bot is cooking up a response...
🍽️ **Recipe: Biryani**
...

🧑‍🍳 You: quit
👋 Happy cooking! Bon appétit!
```

---

## 🧠 How RAG Works in This Project

**RAG (Retrieval-Augmented Generation)** combines information retrieval with language generation:

1. **Retrieval**: When user enters a query, the system searches for semantically similar recipes in the vector database using embeddings
2. **Augmentation**: Retrieved recipes serve as factual context for the LLM
3. **Generation**: The LLM uses this context to generate personalized, accurate responses without hallucinating

**Benefits**:
- ✅ Prevents AI from inventing recipes (grounded in real data)
- ✅ Provides accurate, relevant recommendations
- ✅ Works entirely offline with local models
- ✅ Fast semantic search via vector embeddings

---

## 🔐 Privacy & Local Processing

This entire system runs **locally** on your machine:
- **Ollama**: All LLM inference happens on your CPU/GPU
- **ChromaDB**: Embeddings and vectors stored locally
- **No cloud API calls**: Complete data privacy
- **No internet required**: After models are downloaded

---

## ⚙️ Configuration

Edit these constants in `src/_03_ask_ai.py` to customize:

```python
OLLAMA_BASE_URL = "http://localhost:11434"      # Ollama server URL
EMBEDDING_MODEL = "nomic-embed-text"            # Embedding model
LLM_MODEL = "qwen2.5:1.5b"                      # LLM model
CHROMA_DB_PATH = "../vector_db_recipe"          # Vector DB location
TOP_K_RESULTS = 5                               # Number of retrieved recipes
```

---

## 📊 Data Flow Summary

```
Raw Recipes CSV
      ↓
   [_01_data_prep.ipynb] ← Clean & rename columns
      ↓
Cleaned Recipes CSV
      ↓
   [_02_vector_db.py] ← Embed & store in ChromaDB
      ↓
Vector Database (ChromaDB)
      ↓
   [_03_ask_ai.py] ← Semantic search + LLM generation
      ↓
Formatted Recipe to User
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" | Make sure Ollama is running: `ollama serve` |
| "Model not found" | Download required models: `ollama pull qwen2.5:1.5b` |
| "ChromaDB path not found" | Ensure you've run `_02_vector_db.py` first |
| "No matching recipes" | Try different keywords; query cleaning may remove all words |
| "Slow responses" | Reduce `TOP_K_RESULTS` or use a smaller LLM model |

---

## 🎯 Future Enhancements

- [ ] Web UI with Streamlit
- [ ] Dietary restrictions filtering (vegan, gluten-free, etc.)
- [ ] Cooking time estimation
- [ ] Difficulty level classification
- [ ] Recipe rating system
- [ ] Batch ingredient matching
- [ ] Multi-language support

---

## 📝 License

[Add your license here if applicable]

---

## 👨‍💻 Author

Created as an AI-powered cooking assistant project using RAG principles and local LLMs.

---

**Happy Cooking! 🍽️👨‍🍳**
