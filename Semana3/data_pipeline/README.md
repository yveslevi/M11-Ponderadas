
# Documentação do Projeto Data Pipeline

## Visão Geral

Este projeto consiste em um pipeline de dados construído usando Flask, MinIO e ClickHouse. O pipeline recebe dados JSON através de um endpoint HTTP, processa esses dados, armazena-os em um bucket MinIO como arquivos Parquet e insere-os em uma tabela no ClickHouse. Adicionalmente, há uma integração com a API da Pokedex, permitindo o envio de dados de Pokémon para o pipeline.

## Estrutura do Projeto
O projeto é composto pelos seguintes arquivos:

- app.py: O arquivo principal que define os endpoints e gerencia a lógica do pipeline.
- clickhouse_client.py: Contém funções para interagir com o banco de dados ClickHouse.
- data_processing.py: Contém funções para processar dados e preparar DataFrames para inserção no ClickHouse.
- minio_client.py: Contém funções para interagir com o MinIO, incluindo criação de buckets, upload e download de arquivos.

Estrutura de Pastas

```
/data_pipeline
│
├── app.py
├── data_pipeline/
│   └── clickhouse_client.py
│   └── data_processing.py
│   └── minio_client.py
├── pokedex_integration.py
├── sql/
│   └── create_table.sql
```

Arquivo app.py

Este é o arquivo principal do aplicativo Flask, que define dois endpoints:

POST /data: Recebe dados JSON, processa, armazena no MinIO e insere no ClickHouse.

POST /send-pokemon-data: Integra-se com a API da Pokedex, obtém informações sobre um Pokémon 
e envia os dados para o endpoint /data.

Endpoints
POST /data

Recebe um JSON com a estrutura:
```
{
    "date": 1692345600,
    "dados": 12345
}
```
Validações:

Verifica se os campos date e dados estão presentes.
Verifica se date é um timestamp Unix válido e se dados é um inteiro.
Processamento:

Os dados são processados e armazenados como um arquivo Parquet no MinIO.
O arquivo Parquet é lido e os dados são inseridos na tabela working_data do ClickHouse.
POST /send-pokemon-data
Recebe um JSON opcional com o ID de um Pokémon:

```
{
    "pokemon_id": 1
}
```

Integração com a Pokedex:
Obtém informações sobre o Pokémon com base no ID fornecido.
Gera um JSON no formato esperado pelo endpoint /data e o envia para processamento.
Arquivo clickhouse_client.py
Este arquivo gerencia as interações com o banco de dados ClickHouse.

Funções:
- get_client(): Cria e retorna um cliente ClickHouse.
- execute_sql_script(script_path): Executa um script SQL.
- insert_dataframe(client, table_name, df): Insere um DataFrame em uma tabela do ClickHouse.

Arquivo data_processing.py
Contém funções para processar os dados recebidos.

Funções:
- process_data(data): Converte os dados recebidos em um DataFrame e os salva como um arquivo Parquet.
- prepare_dataframe_for_insert(df): Prepara um DataFrame para inserção no ClickHouse, adicionando colunas de metadados.

Arquivo minio_client.py
Gerencia as interações com o MinIO.

Funções:
- create_bucket_if_not_exists(bucket_name): Cria um bucket no MinIO se ele não existir.
- upload_file(bucket_name, file_path): Faz upload de um arquivo para um bucket MinIO.
- download_file(bucket_name, file_name, local_file_path): Faz download de um arquivo de um - bucket MinIO para o sistema de arquivos local.

Instale as dependências usando:

```
pip install -r requirements.txt
```
Variáveis de Ambiente
O projeto utiliza variáveis de ambiente para configurar as conexões com MinIO e ClickHouse. Essas variáveis devem ser definidas em um arquivo .env na raiz do projeto:

```
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
```
Execução
Para iniciar o servidor Flask, execute:


```
poetry run python .\app.py
```
O servidor estará acessível em http://localhost:5000.

Com ele disponível você poderá testar o envio de requisições a partir da pokedex, conversão para parquet, inserção de dados no minio e db com clickhouse

Testes
Testes podem ser escritos utilizando o framework pytest. Para executar os testes, use o comando:


```
pytest
```
Certifique-se de que as dependências de teste estão instaladas (como pytest e unittest.mock).

## Fazendo passo a passo

1. Criando o pacote

```
poetry new data_pipeline
```

### pyproject.toml

```
cd data_pipeline
poetry add flask requests pandas pyarrow minio clickhouse-connect python-dotenv
```

2. Configurar docker compose com MinIO e ClickHouse
```
version: '3.8'

services:
  minio:
    image: minio/minio:latest
    container_name: minio
    ports:
      - "9000:9000"   # Porta para a API
      - "9001:9001"   # Porta para a Web UI
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data  # Persistência de dados
    command: server /data --console-address ":9001"
    restart: always

  clickhouse:
    image: yandex/clickhouse-server:latest
    container_name: clickhouse
    ports:
      - "8123:8123"  # Porta para a HTTP interface
    volumes:
      - clickhouse_data:/var/lib/clickhouse  # Persistência de dados
    restart: always

volumes:
  minio_data:
    driver: local
  clickhouse_data:
    driver: local
```

Depois é só rodar 
```
docker-compose up --build
```

Na sequência, crie uma pasta sql/ e o arquivo create_table.sql com o código:

```
CREATE TABLE IF NOT EXISTS working_data (
    data_ingestao DateTime,
    dado_linha String,
    tag String
) ENGINE = MergeTree()
ORDER BY data_ingestao;
```

Dentro da pasta data_pipeline crie os arquivos:

- clickhouse_client.py
```
import clickhouse_connect
import os
from dotenv import load_dotenv

load_dotenv()

# Configuração do cliente ClickHouse
CLICKHOUSE_HOST = os.getenv('CLICKHOUSE_HOST')
CLICKHOUSE_PORT = os.getenv('CLICKHOUSE_PORT')

def get_client():
    return clickhouse_connect.get_client(host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT)

def execute_sql_script(script_path):
    client = get_client()
    with open(script_path, 'r') as file:
        sql_script = file.read()
    client.command(sql_script)
    return client

def insert_dataframe(client, table_name, df):
    client.insert_df(table_name, df)
```

- data_processing.py

```
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

def process_data(data):
    # Criar DataFrame e salvar como Parquet
    df = pd.DataFrame([data])
    filename = f"raw_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.parquet"
    table = pa.Table.from_pandas(df)
    pq.write_table(table, filename)
    return filename

def prepare_dataframe_for_insert(df):
    df['data_ingestao'] = datetime.now()
    df['dado_linha'] = df.apply(lambda row: row.to_json(), axis=1)
    df['tag'] = 'example_tag'
    return df[['data_ingestao', 'dado_linha', 'tag']]
```

- minio_client.py

```
from minio import Minio
import os
from dotenv import load_dotenv

load_dotenv()

# Carregar variáveis de ambiente
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')

# Configuração do cliente MinIO
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

def create_bucket_if_not_exists(bucket_name):
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

def upload_file(bucket_name, file_path):
    file_name = os.path.basename(file_path)
    minio_client.fput_object(bucket_name, file_name, file_path)

def download_file(bucket_name, file_name, local_file_path):
    minio_client.fget_object(bucket_name, file_name, local_file_path)

```

e na pasta raiz o app.py


```
from flask import Flask, request, jsonify
from datetime import datetime
from data_pipeline.minio_client import create_bucket_if_not_exists, upload_file, download_file
from data_pipeline.clickhouse_client import execute_sql_script, get_client, insert_dataframe
from data_pipeline.data_processing import process_data, prepare_dataframe_for_insert
import pandas as pd

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

```
e o .env
```
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
```
Depois é só testar as requisições, seja de forma mockada no /data , passando o json abaixo no body:

POST http://localhost:5000/data </br>
Content-Type: application/json
```
{
    "date": 1692345600,
    "dados": 12345
}
```

Ou chamando o endpoint /send_pokemon_data