from supabase import create_client
import os
from datetime import timedelta, datetime

SUPABASE_URL = "https://rqzqxljtkayndylskvdt.supabase.co"
SUPABASE_KEY = "rqzqxljtkayndylskvdt"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_today_price(karat, price):
    supabase.table("gold_price").insert({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "karat": karat,
        "price_per_gram": price
    }).execute()

def save_predictions(karat, predictions):
    for i, price in enumerate(predictions, 1):
        supabase.table("gold_prediction").insert({
            "prediction_date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
            "karat": karat,
            "predicted_price": price
        }).execute()
      
