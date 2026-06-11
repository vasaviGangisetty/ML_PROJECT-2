def calculate_inventory(df):
    # Logic for stock levels
    avg_daily_sales = df['Sales'].mean()
    lead_time = 7 
    safety_stock = avg_daily_sales * 1.5
    reorder_point = (avg_daily_sales * lead_time) + safety_stock
    
    inventory_status = "Good" if df['Sales'].iloc[-1] < reorder_point else "Refill Needed"
    return safety_stock, reorder_point, inventory_status