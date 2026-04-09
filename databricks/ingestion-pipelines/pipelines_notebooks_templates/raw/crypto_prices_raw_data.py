# Databricks notebook source
# DBTITLE 1,Imports
# Imports
import os
import requests
import json
import time
from datetime import datetime

# 1. Configurações para Cripto
target_path = dbutils.widgets.get("target_path")

def fetch_crypto_prices():
    try:
        # Pega preços de Bitcoin e Ethereum em USD
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Adiciona metadados
        data['timestamp_capture'] = datetime.now().isoformat()
        
        dest_dir = target_path.rstrip("/")
        os.makedirs(dest_dir, exist_ok=True)

        filename = f"crypto_{int(time.time())}.json"
        with open(f"{dest_dir}/{filename}", "w") as f:
            json.dump(data, f)
            
        print(f"Crypto Data: BTC ${data['bitcoin']['usd']} | ETH ${data['ethereum']['usd']}")
    except Exception as e:
        print(f"Erro Cripto: {e}")

# Executa 5 vezes
for _ in range(5):
    fetch_crypto_prices()
    time.sleep(10)
