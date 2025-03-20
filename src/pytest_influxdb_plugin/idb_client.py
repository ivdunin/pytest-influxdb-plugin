import logging
from json import dumps
from time import monotonic_ns
from typing import List

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from requests import RequestException

from pytest_influxdb_plugin.constants import RETENTION_POLICY_NAME, RETENTION_POLICY_DURATION

logger = logging.getLogger(__name__)


class IDBClientException(Exception):
    pass


class IDBClient:
    def __init__(self, host: str, port: int = 8086,
                 database: str = 'pytest-influxdb', user: str = '', password: str = '',
                 dry_run: bool = False):

        self._client = InfluxDBClient(host=host, port=port, username=user, password=password, timeout=10)

        if not dry_run:
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
        except (RequestException, InfluxDBClientError) as e:
            raise IDBClientException(f'Cannot switch database: {e}')

    def _check_if_database_exists(self, database_name: str) -> bool:
        """ Check if database exists """
        try:
            return {'name': database_name} in self._client.get_list_database()
        except (RequestException, InfluxDBClientError) as e:
            raise IDBClientException(f'Cannot get list of databases: {e}')

    def close_connection(self):
        """ Close connection to InfluxDB database """
        if self._client:
            logger.info('Close connection')
            try:
                self._client.close()
            except (RequestException, InfluxDBClientError) as e:
                raise IDBClientException(f'Cannot close connection: {e}')

    def write_point(self, point: List[dict], dry_run: bool = False):
        """ Write point to database """
        try:
            if dry_run:
                with open(f'influxdb_metrics_{monotonic_ns()}.json', 'w') as f:
                    f.write(dumps(point, indent=4))
            else:
                self._client.write_points(points=point)
        except (RequestException, InfluxDBClientError) as e:
            raise IDBClientException(f'Cannot write point to database: {e}')

    @property
    def client(self):
        return self._client
