import numpy as np

def calculate_reorder_point(avg_daily_sales, lead_time_days, safety_stock):
    """
    ROP = (Average Daily Sales * Lead Time) + Safety Stock
    """
    return (avg_daily_sales * lead_time_days) + safety_stock

def calculate_safety_stock(max_daily_sales, max_lead_time, avg_daily_sales, avg_lead_time):
    """
    Safety Stock = (Max Sales * Max Lead Time) - (Avg Sales * Avg Lead Time)
    """
    return (max_daily_sales * max_lead_time) - (avg_daily_sales * avg_lead_time)