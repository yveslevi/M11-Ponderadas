import requests
import time

def get_pokemon_data(pokemon_id):
    response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{pokemon_id}')
    if response.status_code == 200:
        return response.json()
    else:
        return None

def generate_json_from_pokemon(pokemon_data):
    if pokemon_data:
        json_data = {
            "date": int(time.time()),
            "dados": pokemon_data['id']
        }
        return json_data
    return None

def post_data_to_api(json_data):
    if json_data:
        response = requests.post('http://localhost:5000/data', json=json_data)
        if response.status_code == 200:
            print("Dados enviados com sucesso!")
        else:
            print("Erro ao enviar dados:", response.json())
    else:
        print("JSON inválido, não enviado.")
