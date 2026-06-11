import pandas as pd

def clean_and_process(df):
    # 1. Convert Date column
    # We look for common date names
    date_col = None
    for col in df.columns:
        if 'date' in col.lower():
            date_col = col
            break
    
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 2. Add Seasonal Features
        def get_season(month):
            if month in [12, 1, 2]: return 'Winter'
            if month in [3, 4, 5]: return 'Spring'
            if month in [6, 7, 8]: return 'Summer'
            return 'Autumn'
        
        df['Month'] = df[date_col].dt.month
        df['Year'] = df[date_col].dt.year
        df['Season'] = df['Month'].apply(get_season)
    
    # 3. Handle Missing Values
    df = df.ffill().bfill()
    
    # 4. Outlier Handling (Simple Clip)
    if 'Sales' in df.columns:
        q_low = df["Sales"].quantile(0.01)
        q_hi  = df["Sales"].quantile(0.99)
        df["Sales"] = df["Sales"].clip(lower=q_low, upper=q_hi)
        
    return df