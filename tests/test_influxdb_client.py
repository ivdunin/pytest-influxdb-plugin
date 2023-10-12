from influxdb import InfluxDBClient

from pytest_influxdb_plugin.idb_client import IDBClient


def test_client_database_exists(monkeypatch):
    monkeypatch.setattr(IDBClient, '_check_if_database_exists', lambda self, db: True)
    with IDBClient(host='localhost') as client:
        assert isinstance(client.client, InfluxDBClient), 'Incorrect type of client'


def test_client_database_not_exists(monkeypatch):
    monkeypatch.setattr(IDBClient, '_check_if_database_exists', lambda self, db: False)
    monkeypatch.setattr(InfluxDBClient, 'create_database', lambda self, db: None)
    monkeypatch.setattr(InfluxDBClient, 'create_retention_policy', lambda self, **kwargs: None)
    with IDBClient(host='localhost') as client:
        assert isinstance(client.client, InfluxDBClient), 'Incorrect type of client'
