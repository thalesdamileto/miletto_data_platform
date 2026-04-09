# Databricks notebook source
# DBTITLE 1,Imports
# Imports
import requests
import json

# 1. Configurações para Pokémon
output_path_poke = "/Volumes/workspace/default/raw/pokemon_data/"

def fetch_pokemon_data(pokemon_name):
    try:
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Selecionamos apenas algumas infos para o log, mas salvamos o JSON inteiro
        filename = f"poke_{pokemon_name}.json"
        with open(f"{output_path_poke}{filename}", "w") as f:
            json.dump(data, f)
            
        print(f"Sucesso: Dados de {pokemon_name} capturados. Peso: {data['weight']}")
    except Exception as e:
        print(f"Erro Pokémon: {e}")

# Exemplo pegando uma lista de eventos/entidades
for p in ["pikachu", "charizard", "bulbasaur"]:
    fetch_pokemon_data(p)
