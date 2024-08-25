import unittest
from flask import Flask
from app import app
import json
from minio import Minio 
from minio.error import S3Error

class BasicTests(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        self.app = app.test_client()
        self.assertEqual(app.debug, False)

    def test_receive_data_success(self):
        # Exemplo de dados válidos
        data = {
            "date": 1692345600,
            "dados": 12345
        }
        response = self.app.post('/data', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Dados recebidos, armazenados e processados com sucesso', response.get_data(as_text=True))

    def test_receive_data_missing_fields(self):
        # Teste com campos faltando
        data = {
            "date": 1692345600
        }
        response = self.app.post('/data', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Formato de dados inválido', response.get_data(as_text=True))

    def test_receive_data_invalid_data(self):
        # Teste com dados inválidos
        data = {
            "date": "invalid_date",
            "dados": "invalid_dados"
        }
        response = self.app.post('/data', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Tipo de dados inválido', response.get_data(as_text=True))

if __name__ == "__main__":
    unittest.main()
