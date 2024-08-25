from flask import Flask, request, jsonify
from datetime import datetime
from data_pipeline.minio_client import create_bucket_if_not_exists, upload_file, download_file
from data_pipeline.clickhouse_client import execute_sql_script, get_client, insert_dataframe
from data_pipeline.data_processing import process_data, prepare_dataframe_for_insert
from pokedex_integration import get_pokemon_data, generate_json_from_pokemon, post_data_to_api
import pandas as pd
from minio import Minio 
from minio.error import S3Error

app = Flask(__name__)

# Criar bucket se não existir
create_bucket_if_not_exists("raw-data")

# Executar o script SQL para criar a tabela
execute_sql_script('sql/create_table.sql')

@app.route('/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    if not data or 'date' not in data or 'dados' not in data:
        return jsonify({"error": "Formato de dados inválido"}), 400

    try:
        datetime.fromtimestamp(data['date'])
        int(data['dados'])
    except (ValueError, TypeError):
        return jsonify({"error": "Tipo de dados inválido"}), 400

    # Processar e salvar dados
    filename = process_data(data)
    upload_file("raw-data", filename)

    # Ler arquivo Parquet do MinIO
    download_file("raw-data", filename, f"downloaded_{filename}")
    df_parquet = pd.read_parquet(f"downloaded_{filename}")

    # Preparar e inserir dados no ClickHouse
    df_prepared = prepare_dataframe_for_insert(df_parquet)
    client = get_client()  # Obter o cliente ClickHouse
    insert_dataframe(client, 'working_data', df_prepared)

    return jsonify({"message": "Dados recebidos, armazenados e processados com sucesso"}), 200

@app.route('/send-pokemon-data', methods=['POST'])
def send_pokemon_data():
    pokemon_id = request.json.get('pokemon_id', 1)  # Recebe o ID do Pokémon via request JSON
    pokemon_data = get_pokemon_data(pokemon_id)
    json_data = generate_json_from_pokemon(pokemon_data)
    post_data_to_api(json_data)
    return jsonify({"message": "Dados do Pokémon enviados!"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)