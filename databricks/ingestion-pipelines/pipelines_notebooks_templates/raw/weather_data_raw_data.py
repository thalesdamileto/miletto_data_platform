# Databricks notebook source
# DBTITLE 1,Imports
# Imports
import os
import requests
import json
import time
from datetime import datetime

# 1. Configurações para Clima
target_path = dbutils.widgets.get("target_path")
API_KEY = "SUA_CHAVE_AQUI" 

def fetch_weather_data(city="Sao Paulo"):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        dest_dir = target_path.rstrip("/")
        os.makedirs(dest_dir, exist_ok=True)

        filename = f"weather_{city}_{int(time.time())}.json"
        with open(f"{dest_dir}/{filename}", "w") as f:
            json.dump(data, f)
            
        temp = data['main']['temp']
        print(f"Clima em {city}: {temp}°C")
    except Exception as e:
        print(f"Erro Weather: {e} (Verifique sua API Key)")

# Executa para 3 cidades diferentes
for cidade in ["Sao Paulo", "London", "Tokyo"]:
    fetch_weather_data(cidade)
    time.sleep(2)
