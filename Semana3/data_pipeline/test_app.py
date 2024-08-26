import pytest
from flask import Flask
from app import app
import json
from unittest.mock import patch
from minio import Minio
from minio.error import S3Error

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    yield client

@patch('data_pipeline.minio_client.upload_file')
@patch('data_pipeline.minio_client.download_file')
def test_receive_data_success(mock_upload, mock_download, client):
    data = {
        "date": 1692345600,
        "dados": 12345
    }
    response = client.post('/data', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    assert 'Dados recebidos, armazenados e processados com sucesso' in response.get_data(as_text=True)

def test_receive_data_missing_fields(client):
    data = {
        "date": 1692345600
    }
    response = client.post('/data', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 400
    assert 'Formato de dados inválido' in response.get_data(as_text=True)

def test_receive_data_invalid_data(client):
    data = {
        "date": "invalid_date",
        "dados": "invalid_dados"
    }
    response = client.post('/data', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 400
    assert 'Tipo de dados inválido' in response.get_data(as_text=True)
