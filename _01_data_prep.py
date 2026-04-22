import pandas as pd
import ast

def clean_text(text, separator=", "):
    """Converts a stringified list into a clean joined string."""
    try:
        # Converts "['apple', 'banana']" into an actual Python list ['apple', 'banana']
        actual_list = ast.literal_eval(text)
        # Joins the list into a clean string: "apple, banana"
        return separator.join(actual_list)
    except:
        # If it fails (e.g., it's already a normal string), just return the original text
        return text

def load_and_clean_data(csv_path, sample_size=10000):
    print("Loading dataset...")
    df = pd.read_csv(csv_path, nrows=sample_size)
    
    df = df[['title', 'ingredients', 'directions']]
    df = df.dropna()
    
    print("Cleaning up list formats...")
    # Apply our cleaning function to make the text pretty
    df['ingredients'] = df['ingredients'].apply(lambda x: clean_text(x, separator=", "))
    df['directions'] = df['directions'].apply(lambda x: clean_text(x, separator=" "))
    
    print(f"Success! {len(df)} recipes cleaned and ready.")
    return df

if __name__ == "__main__":
    recipe_df = load_and_clean_data('./dataset/full_dataset.csv')
    
    print("\nData Preview:")
    print(recipe_df.head(2))