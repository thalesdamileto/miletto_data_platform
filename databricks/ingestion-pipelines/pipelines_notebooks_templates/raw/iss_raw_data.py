# Databricks notebook source
# DBTITLE 1,Imports
# Imports
import os
import requests
import json
import time
from datetime import datetime

# 1. Configurações de Destino
target_path = dbutils.widgets.get("target_path")

def fetch_and_save_iss_data():
    try:
        # 2. Requisição à API Pública
        response = requests.get("http://api.open-notify.org/iss-now.json")
        response.raise_for_status()
        data = response.json()
        
        # Adicionamos um timestamp de processamento para facilitar o particionamento depois
        data['ingested_at'] = datetime.now().isoformat()
        
        # 3. Garantir diretório no Volume (job JSON não cria pastas)
        dest_dir = target_path.rstrip("/")
        os.makedirs(dest_dir, exist_ok=True)

        filename = f"iss_data_{int(time.time())}.json"
        full_path = f"{dest_dir}/{filename}"
        print(data)

        # 4. Salvar no Volume UC
        with open(full_path, "w") as f:
            json.dump(data, f)
            
        print(f"Sucesso! Arquivo salvo em: {full_path}")
        
    except Exception as e:
        print(f"Erro na requisição: {e}")

# Simulação: Rodar 5 vezes para gerar dados para o seu pipeline
for _ in range(20):
    fetch_and_save_iss_data()
    time.sleep(5) # Espera 5 segundos entre as chamadas
    