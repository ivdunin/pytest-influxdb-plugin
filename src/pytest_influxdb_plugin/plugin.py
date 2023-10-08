import logging

import pytest

from pytest_influxdb_plugin.idb_client import IDBClient

logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    group_influx = parser.getgroup('influxdb-plugin')
    group_influx.addoption('--influx-host', dest='idb_host', type=str, default='', help='InfluxDB host')
    group_influx.addoption('--influx-port', dest='idb_port', default=8086, help='InfluxDB port')
    group_influx.addoption('--influx-user', dest='idb_user', default='', help='InfluxDB user')
    group_influx.addoption('--influx-password', dest='idb_password', default='', help='InfluxDB password')
    group_influx.addoption('--influx-db', dest='idb_db', default='pytest-influxdb', help='InfluxDB database name')
    group_influx.addoption('--use-original-name', action='store_true', dest='use_original_name',
                           help='Use original test name instead of node name.')

    group_idb_tags = parser.getgroup('influxdb-tags')
    group_idb_tags.addoption('--build-number', dest='build_number', help='CI build number')
    group_idb_tags.addoption('--build-name', dest='build_name', help='CI build name')
    group_idb_tags.addoption('--parent-build-number', dest='parent_build_number', help='CI parent build number')
    group_idb_tags.addoption('--parent-build-name', dest='parent_build_name', help='CI parent build name')


@pytest.fixture(name='idb_client', scope='session', autouse=True)
def fixture_idb_client(request):
    """ Fixture which initialize InfluxDB client and create database if it doesn't exist """
    opt = request.config.option

    if opt.idb_host != '':

        client = IDBClient(host=opt.idb_host,
                           port=opt.idb_port,
                           database=opt.idb_db,
                           user=opt.idb_user,
                           password=opt.idb_password)

        yield client

        client.close_connection()
    else:
        yield
