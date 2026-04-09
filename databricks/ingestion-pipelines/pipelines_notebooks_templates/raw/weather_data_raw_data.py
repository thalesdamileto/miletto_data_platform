# Databricks notebook source
# DBTITLE 1,Imports
# Imports
import requests
import json
import time
from datetime import datetime

# 1. Configurações para Clima
output_path_weather = "/Volumes/workspace/default/raw/weather_data/"
API_KEY = "SUA_CHAVE_AQUI" 

def fetch_weather_data(city="Sao Paulo"):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        filename = f"weather_{city}_{int(time.time())}.json"
        with open(f"{output_path_weather}{filename}", "w") as f:
            json.dump(data, f)
            
        temp = data['main']['temp']
        print(f"Clima em {city}: {temp}°C")
    except Exception as e:
        print(f"Erro Weather: {e} (Verifique sua API Key)")

# Executa para 3 cidades diferentes
for cidade in ["Sao Paulo", "London", "Tokyo"]:
    fetch_weather_data(cidade)
    time.sleep(2)
