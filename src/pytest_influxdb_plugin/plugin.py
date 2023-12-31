import logging
from typing import Dict

import pytest
from _pytest.nodes import Item
from _pytest.reports import CollectReport
from _pytest.stash import StashKey

from pytest_influxdb_plugin.idb_client import IDBClient, IDBClientException
from pytest_influxdb_plugin.pytest_object import PytestObject

logger = logging.getLogger(__name__)
report_key = StashKey[Dict[str, CollectReport]]()
call_key = StashKey[Dict[str, CollectReport]]()


def pytest_addoption(parser):
    group_influx = parser.getgroup('influxdb-plugin', description='InfluxDB Configuration')
    group_influx.addoption('--influx-host', dest='idb_host', type=str, default='', help='InfluxDB host')
    group_influx.addoption('--influx-port', dest='idb_port', type=int, default=8086, help='InfluxDB port')
    group_influx.addoption('--influx-user', dest='idb_user', default='', help='InfluxDB user')
    group_influx.addoption('--influx-password', dest='idb_password', default='', help='InfluxDB password')
    group_influx.addoption('--influx-db', dest='idb_db', default='pytest-influxdb', help='InfluxDB database name')
    group_influx.addoption('--raise-influxdb-errors', action='store_true',
                           help='Raise InfluxDB exceptions. Default: suppress exceptions')

    group_idb_tags = parser.getgroup('influxdb-tags', description='Additional tags for tests')
    group_idb_tags.addoption('--build-number', dest='build_number', help='CI build number')
    group_idb_tags.addoption('--build-name', dest='build_name', help='CI build name')
    group_idb_tags.addoption('--parent-build-number', dest='parent_build_number', help='CI parent build number')
    group_idb_tags.addoption('--parent-build-name', dest='parent_build_name', help='CI parent build name')


def pytest_configure(config: pytest.Config):
    """ Configure InfluxDB

    If idb_host variable exists init InfluxDB client and store it in global namespace
    """
    opts = config.option

    if opts.idb_host:
        try:
            client = IDBClient(host=opts.idb_host, port=opts.idb_port,
                               database=opts.idb_db, user=opts.idb_user, password=opts.idb_password)

            pytest._influxdb_client = client
        except IDBClientException as e:
            logger.error(f'Cannot create InfluxDB connection: {e}')
            if opts.raise_influxdb_errors:
                raise e


def pytest_unconfigure(config: pytest.Config):
    """ At the end of test session close connection to InfluxDB """
    client: IDBClient = getattr(pytest, '_influxdb_client', None)
    if client:
        try:
            client.close_connection()
        except IDBClientException as e:
            logger.error(f'Cannot close connection: {e}')
            if config.option.raise_influxdb_errors:
                raise e


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    item.stash.setdefault(report_key, {})[report.when] = report
    item.stash.setdefault(call_key, {})[report.when] = call


@pytest.hookimpl(trylast=True, hookwrapper=True)
def pytest_runtest_protocol(item: Item, nextitem: Item):
    yield

    client: IDBClient = getattr(pytest, '_influxdb_client', None)
    if client:
        reports = item.stash[report_key]
        calls = item.stash[call_key]

        try:
            data = PytestObject(item, reports, calls).to_dict()
            client.write_point(data)
        except IDBClientException as e:
            logger.error(f'Cannot write point for test: {item.nodeid}.\nReason: {e}')
            if item.config.option.raise_influxdb_errors:
                raise e

