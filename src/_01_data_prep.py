import pandas as pd

def clean_data(df):
    print('cleaning the dataset!')
    
    df = df.rename(columns={
        'TranslatedRecipeName': 'title',
        'TranslatedIngredients': 'ingredients',
        'TranslatedInstructions': 'directions'
    })
    
    df = df[['title', 'ingredients', 'directions']]
    
    df = df.dropna()
    
    df.to_csv('../dataset/_02_cleaned/recipes_cleaned.csv')
    
    print('cleaned the dataset successfully!')

if __name__ == '__main__':
    df = pd.read_csv('../dataset/_01_raw/recipes.csv')
    clean_data(df)