# Databricks notebook source
# DBTITLE 1,Imports
# Imports
import requests
import json
import time
from datetime import datetime

# 1. Configurações para Cripto
target_path = "/Volumes/workspace/default/raw/crypto_prices/"

def fetch_crypto_prices():
    try:
        # Pega preços de Bitcoin e Ethereum em USD
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Adiciona metadados
        data['timestamp_capture'] = datetime.now().isoformat()
        
        filename = f"crypto_{int(time.time())}.json"
        with open(f"{target_path}{filename}", "w") as f:
            json.dump(data, f)
            
        print(f"Crypto Data: BTC ${data['bitcoin']['usd']} | ETH ${data['ethereum']['usd']}")
    except Exception as e:
        print(f"Erro Cripto: {e}")

# Executa 5 vezes
for _ in range(5):
    fetch_crypto_prices()
    time.sleep(10)
