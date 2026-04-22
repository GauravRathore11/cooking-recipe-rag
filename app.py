"""
app.py — Streamlit UI for the RAG-powered Recipe Bot.
Run with: streamlit run app.py
"""

import time
import streamlit as st
import chromadb
from chromadb.utils import embedding_functions
from ollama import Client as OllamaClient

from prompts import SYSTEM_PROMPT, RECIPE_OUTPUT_FORMAT, RAG_QUERY_PROMPT

# ─── Configuration ───────────────────────────────────────────────────────────

OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "llama3"
CHROMA_DB_PATH = "./recipe_db"
COLLECTION_NAME = "recipes"
TOP_K_RESULTS = 5


# ─── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Recipe Bot — AI Kitchen Assistant",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── Custom CSS ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: linear-gradient(160deg, #0f0c29 0%, #1a1333 40%, #24243e 100%);
    }

    /* ── Header area ── */
    .hero-container {
        text-align: center;
        padding: 2rem 1rem 1rem 1rem;
    }
    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #a09cb8;
        font-weight: 400;
        margin-bottom: 1.5rem;
    }

    /* ── Glassmorphism card ── */
    .glass-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.8rem;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        margin-bottom: 1.2rem;
        transition: border-color 0.3s ease;
    }
    .glass-card:hover {
        border-color: rgba(247, 151, 30, 0.25);
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #16132b 0%, #1c1836 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #ffd200 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: #c4bfda !important;
    }

    /* ── Chat messages ── */
    .stChatMessage {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 14px !important;
        padding: 0.5rem !important;
        margin-bottom: 0.6rem !important;
    }

    /* ── Chat input ── */
    .stChatInput > div {
        border-radius: 14px !important;
        border: 1px solid rgba(247, 151, 30, 0.3) !important;
        background: rgba(255,255,255,0.04) !important;
    }
    .stChatInput > div:focus-within {
        border-color: #ffd200 !important;
        box-shadow: 0 0 0 2px rgba(255, 210, 0, 0.15) !important;
    }

    /* ── Metric / stat cards ── */
    .stat-pill {
        display: inline-block;
        background: rgba(247, 151, 30, 0.12);
        border: 1px solid rgba(247, 151, 30, 0.25);
        border-radius: 999px;
        padding: 0.35rem 1rem;
        color: #ffd200;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }

    /* ── Time pill (for generation timer) ── */
    .time-pill {
        display: inline-block;
        background: rgba(80, 200, 120, 0.12);
        border: 1px solid rgba(80, 200, 120, 0.25);
        border-radius: 999px;
        padding: 0.35rem 1rem;
        color: #50c878;
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 0.6rem;
    }

    /* ── Suggestion chips ── */
    .chip-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.8rem;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }

    /* ── Divider override ── */
    hr { border-color: rgba(255,255,255,0.06) !important; }

    /* ── Status / spinner ── */
    .stSpinner > div > div {
        border-top-color: #ffd200 !important;
    }
</style>
""", unsafe_allow_html=True)


# ─── Cached Resources ───────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_collection():
    """Load the ChromaDB collection once and cache it across reruns."""
    db_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        url=OLLAMA_BASE_URL,
        model_name=EMBEDDING_MODEL,
    )
    collection = db_client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=ollama_ef,
    )
    return collection


def search_recipes(collection, query: str, n_results: int = TOP_K_RESULTS):
    """Semantic search against ChromaDB. Returns (context_string, raw_results)."""
    results = collection.query(query_texts=[query], n_results=n_results)

    if not results or not results["metadatas"] or not results["metadatas"][0]:
        return None, None

    context_parts = []
    for i, meta in enumerate(results["metadatas"][0], start=1):
        context_parts.append(
            f"Recipe {i}: {meta.get('title', 'Unknown')}\n"
            f"  Ingredients: {meta.get('ingredients', 'N/A')}\n"
            f"  Instructions: {meta.get('instructions', 'N/A')}\n"
        )

    return "\n".join(context_parts), results["metadatas"][0]


def stream_llm_response(user_query: str, context: str):
    """Generator that yields tokens from Ollama for streaming into st.write_stream."""
    client = OllamaClient(host=OLLAMA_BASE_URL)

    full_user_prompt = RAG_QUERY_PROMPT.format(
        context=context,
        user_query=user_query,
    )

    stream = client.chat(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + RECIPE_OUTPUT_FORMAT},
            {"role": "user", "content": full_user_prompt},
        ],
        stream=True,
    )

    for chunk in stream:
        yield chunk["message"]["content"]


def format_elapsed(seconds: float) -> str:
    """Format elapsed seconds into a human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins}m {secs:.1f}s"


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.divider()

    # Model picker
    llm_choice = st.selectbox(
        "LLM Model",
        options=["llama3", "qwen2.5", "qwen2.5:0.5b"],
        index=0,
        help="Select the Ollama model to generate recipes.",
    )
    LLM_MODEL = llm_choice

    top_k = st.slider(
        "Recipes to retrieve", min_value=1, max_value=10, value=TOP_K_RESULTS,
        help="How many recipes to pull from the vector DB as context."
    )

    st.divider()

    # Load collection & show stats
    try:
        collection = load_collection()
        recipe_count = collection.count()
        st.markdown("### 📊 Database")
        st.markdown(
            f'<span class="stat-pill">🗄️ {recipe_count:,} recipes</span>'
            f'<span class="stat-pill">🧠 {EMBEDDING_MODEL}</span>',
            unsafe_allow_html=True,
        )
        db_ready = True
    except Exception as e:
        st.error(f"⚠️ Cannot connect to recipe DB: {e}")
        db_ready = False

    st.divider()
    st.markdown("### 💡 Try asking")
    suggestions = [
        "I have chicken, garlic, and lemon",
        "How to make french onion soup?",
        "Give me a pasta recipe with tomatoes",
        "I have eggs, cheese, and spinach",
        "Chocolate cake recipe",
    ]
    for s in suggestions:
        st.markdown(f"- *{s}*")

    st.divider()
    st.caption("Built with Ollama · ChromaDB · Streamlit")


# ─── Hero Header ─────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero-container">
    <div class="hero-title">🍳 Recipe Bot</div>
    <div class="hero-subtitle">Your AI-powered kitchen assistant — tell me your ingredients or ask for a dish!</div>
</div>
""", unsafe_allow_html=True)


# ─── Chat History ────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hey there, chef! 👋\n\n"
                "I can help you cook something amazing. Just tell me:\n\n"
                "- **What ingredients you have** — e.g. *chicken, garlic, butter*\n"
                "- **A dish you'd like to make** — e.g. *french onion soup*\n\n"
                "I'll search through my recipe database and cook up a detailed recipe for you! 🍽️"
            ),
        }
    ]

# Render past messages
for msg in st.session_state.messages:
    avatar = "🍳" if msg["role"] == "assistant" else "🧑‍🍳"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])


# ─── Chat Input ──────────────────────────────────────────────────────────────

if prompt := st.chat_input("Enter ingredients or dish name...", disabled=not db_ready):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍🍳"):
        st.markdown(prompt)

    # Process
    with st.chat_message("assistant", avatar="🍳"):
        overall_start = time.time()

        # ── Step 1: Retrieve from Vector DB ──────────────────────────────
        with st.status("🔍 Searching recipe database...", expanded=True) as status:
            search_start = time.time()
            context, raw_results = search_recipes(collection, prompt, n_results=top_k)
            search_time = time.time() - search_start

            if not context:
                status.update(label="❌ No matching recipes found", state="error", expanded=False)
                response = "😕 Sorry, I couldn't find any matching recipes in the database. Try different ingredients or a dish name!"
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.stop()

            # Show what was found
            st.markdown(f"Found **{len(raw_results)}** matching recipes in **{search_time:.2f}s**")
            for i, meta in enumerate(raw_results, start=1):
                st.markdown(
                    f"&ensp;{i}. **{meta.get('title', 'Unknown')}** — "
                    f"_{meta.get('ingredients', 'N/A')[:70]}..._"
                )
            status.update(
                label=f"✅ Retrieved {len(raw_results)} recipes ({search_time:.2f}s)",
                state="complete",
                expanded=False,
            )

        # ── Step 2: Generate with LLM (with live timer) ──────────────────
        with st.status(
            f"👨‍🍳 Chef Bot is cooking with **{LLM_MODEL}**... (loading model)",
            expanded=True,
        ) as gen_status:
            # Show a live "waiting" message while model loads
            timer_placeholder = st.empty()
            gen_start = time.time()

            # Get the generator — the first token may take a long time (model loading)
            token_gen = stream_llm_response(prompt, context)

            # Wait for the first token while updating the timer
            first_token = None
            for token in token_gen:
                first_token = token
                break  # Got the first token, now update and move to streaming

            first_token_time = time.time() - gen_start
            timer_placeholder.markdown(
                f"Model loaded in **{first_token_time:.1f}s** — now streaming response..."
            )

            gen_status.update(
                label=f"✍️ Generating recipe with **{LLM_MODEL}**...",
                state="running",
                expanded=False,
            )

        # ── Step 3: Stream the actual response ───────────────────────────
        def stream_with_first_token():
            """Re-yield the first token we already consumed, then the rest."""
            if first_token is not None:
                yield first_token
            yield from token_gen

        response = st.write_stream(stream_with_first_token())

        # ── Summary timing ───────────────────────────────────────────────
        total_time = time.time() - overall_start
        gen_time = time.time() - gen_start

        st.markdown(
            f'<div class="time-pill">'
            f'⏱️ Search: {search_time:.1f}s &nbsp;·&nbsp; '
            f'Model load: {first_token_time:.1f}s &nbsp;·&nbsp; '
            f'Generation: {format_elapsed(gen_time)} &nbsp;·&nbsp; '
            f'Total: {format_elapsed(total_time)}'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.session_state.messages.append({"role": "assistant", "content": response})
