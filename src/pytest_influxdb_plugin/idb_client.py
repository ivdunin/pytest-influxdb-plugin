import logging

import requests
from influxdb import InfluxDBClient

logger = logging.getLogger(__name__)

RETENTION_POLICY_NAME = '90days'
RETENTION_POLICY_DURATION = '90d'


class IDBClientException(Exception):
    pass


class IDBClient:
    def __init__(self, host: str, port: int = 8086,
                 database: str = 'pytest-influxdb', user: str = '', password: str = ''):
        self._client = InfluxDBClient(host=host, port=port, username=user, password=password)
        self._switch_database(database_name=database)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    def _switch_database(self, database_name: str):
        """ Switch to database and create it if database not exists """
        try:
            if not self._check_if_database_exists(database_name):
                self._client.create_database(database_name)
                self._client.create_retention_policy(name=RETENTION_POLICY_NAME,
                                                     duration=RETENTION_POLICY_DURATION,
                                                     replication='1',
                                                     database=database_name,
                                                     default=True)
                logger.info('Database successfully created with retention policy')

            self._client.switch_database(database_name)
            logger.info(f'Database switched to: {database_name}')
        except requests.exceptions.ConnectionError as e:
            raise IDBClientException(f'Cannot switch database: {e}')

    def _check_if_database_exists(self, database_name: str) -> bool:
        """ Check if database exists """
        try:
            for db in self._client.get_list_database():
                if db['name'] == database_name:
                    return True
            return False
        except requests.exceptions.ConnectionError as e:
            raise IDBClientException(f'Cannot get list of databases: {e}')

    def close_connection(self):
        """ Close connection to InfluxDB database """
        if self._client:
            self._client.close()

    @property
    def client(self):
        return self._client
