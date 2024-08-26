import pytest
from unittest.mock import patch, MagicMock
from app import app
from minio import minio

@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()

def test_receive_data_success(client):
    data = {
        "date": 1692345600,
        "dados": 12345
    }
    with patch('data_pipeline.minio_client.upload_file') as mock_upload, \
         patch('data_pipeline.minio_client.download_file') as mock_download, \
         patch('pandas.read_parquet', return_value=pd.DataFrame([data])) as mock_parquet, \
         patch('data_pipeline.clickhouse_client.insert_dataframe') as mock_insert:

        response = client.post('/data', json=data)
        assert response.status_code == 200
        assert 'Dados recebidos, armazenados e processados com sucesso' in response.get_data(as_text=True)

def test_receive_data_invalid_format(client):
    data = {
        "date": "invalid_date",
        "dados": "invalid_dados"
    }
    response = client.post('/data', json=data)
    assert response.status_code == 400
    assert 'Tipo de dados inválido' in response.get_data(as_text=True)

def test_receive_data_minio_failure(client):
    data = {
        "date": 1692345600,
        "dados": 12345
    }
    with patch('data_pipeline.minio_client.upload_file', side_effect=S3Error("Mocked error", "Test")) as mock_upload:
        response = client.post('/data', json=data)
        assert response.status_code == 500
        assert 'Erro ao salvar dados' in response.get_data(as_text=True)
