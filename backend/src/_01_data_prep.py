import pandas as pd
import os

# Build paths relative to this file's location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def clean_data(df):
    print('cleaning the dataset!')
    
    df = df.rename(columns={
        'TranslatedRecipeName': 'title',
        'TranslatedIngredients': 'ingredients',
        'TranslatedInstructions': 'directions'
    })
    
    df = df[['title', 'ingredients', 'directions']]
    
    df = df.dropna()
    
    output_path = os.path.join(BASE_DIR, 'dataset', '_02_cleaned', 'recipes_cleaned.csv')
    df.to_csv(output_path)
    
    print('cleaned the dataset successfully!')

if __name__ == '__main__':
    input_path = os.path.join(BASE_DIR, 'dataset', '_01_raw', 'recipes.csv')
    df = pd.read_csv(input_path)
    clean_data(df)