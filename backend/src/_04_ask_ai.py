from ollama import Client as OllamaClient
from utils.prompts import SYSTEM_PROMPT, RECIPE_OUTPUT_FORMAT, RAG_QUERY_PROMPT
from utils.functions import get_recipe_collection
from dotenv import load_dotenv
from _03_rag import search_recipes
import os
from utils.functions import clean_query

load_dotenv()

EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL')
LLM_MODEL = os.getenv('LLM_MODEL')


def ask_llm(user_query: str, context: str):
    client = OllamaClient(host=OLLAMA_BASE_URL)

    full_user_prompt = RAG_QUERY_PROMPT.format(
        context=context,
        user_query=user_query
    )

    print("\nChef Bot is generating response...\n")
    print("-" * 60)

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

    print("\n" + "-" * 60)
    return full_response


def main():
    print("\n" + "=" * 60)
    print("   RECIPE BOT — AI Kitchen Assistant")
    print("=" * 60)
    print("\nEnter ingredients or a dish name.")
    print("Type 'quit' to exit.\n")

    collection = get_recipe_collection()

    while True:
        print()
        user_input = input("You: ").strip()

        if not user_input:
            print("Please enter something!")
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("\nGoodbye! Happy cooking!")
            break

        cleaned_query = clean_query(user_input)
        context = search_recipes(collection, cleaned_query)

        if not context:
            print("No matching recipes found.")
            continue

        ask_llm(user_input, context)


if __name__ == "__main__":
    main()