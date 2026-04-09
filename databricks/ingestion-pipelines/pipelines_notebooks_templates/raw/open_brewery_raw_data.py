# Databricks notebook source
# DBTITLE 1,Imports
import requests
import json
import time
from datetime import datetime

# 1. Configurações de Destino
# Criamos uma pasta específica para os dados de cervejarias
output_path = "/Volumes/workspace/default/raw/brewery_data/" 

def fetch_and_save_brewery_data():
    try:
        # 2. Requisição à API Pública (Pegando as primeiras 50 cervejarias como exemplo)
        # Documentação: https://www.openbrewerydb.org/documentation
        url = "https://api.openbrewerydb.org/v1/breweries?per_page=50"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Estrutura de metadados para o log
        payload = {
            "ingested_at": datetime.now().isoformat(),
            "count": len(data),
            "results": data
        }
        
        # 3. Nome do arquivo único
        filename = f"breweries_{int(time.time())}.json"
        full_path = f"{output_path}{filename}"
        
        # 4. Salvar no Volume do Unity Catalog
        # Certifique-se de que o diretório existe ou o Databricks tenha permissão para criar
        with open(full_path, "w") as f:
            json.dump(payload, f)
            
        print(f"Sucesso! {len(data)} cervejarias salvas em: {full_path}")
        
    except Exception as e:
        print(f"Erro na extração: {e}")

# Simulação: Rodar 3 vezes com intervalo de 10 segundos
# Reduzi o range para 3 para evitar excesso de chamadas desnecessárias na API pública
for _ in range(3):
    fetch_and_save_brewery_data()
    time.sleep(10)
