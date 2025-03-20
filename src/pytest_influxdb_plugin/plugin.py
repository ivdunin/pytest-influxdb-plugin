import logging
from typing import Dict

import pytest
from _pytest.nodes import Item
from _pytest.reports import CollectReport
from _pytest.stash import StashKey

from pytest_influxdb_plugin.constants import EXTRA_FIELDS, EXTRA_TAGS
from pytest_influxdb_plugin.idb_client import IDBClient, IDBClientException
from pytest_influxdb_plugin.pytest_object import PytestObject

logger = logging.getLogger(__name__)
report_key = StashKey[Dict[str, CollectReport]]()
call_key = StashKey[Dict[str, CollectReport]]()
extra_values = StashKey[Dict[str, dict]]()


def pytest_addoption(parser):
    group_influx = parser.getgroup('influxdb-plugin', description='InfluxDB Configuration')
    group_influx.addoption('--influxdb-host', dest='idb_host', type=str, default='', help='InfluxDB host')
    group_influx.addoption('--influxdb-port', dest='idb_port', type=int, default=8086, help='InfluxDB port')
    group_influx.addoption('--influxdb-user', dest='idb_user', default='', help='InfluxDB user')
    group_influx.addoption('--influxdb-password', dest='idb_password', default='', help='InfluxDB password')
    group_influx.addoption('--influxdb-db', dest='idb_db', default='pytest-influxdb', help='InfluxDB database name')
    group_influx.addoption('--raise-influxdb-errors', action='store_true',
                           help='Raise InfluxDB exceptions. Default: suppress exceptions')
    group_influx.addoption('--influxdb-dry-run', action='store_true', help='Save metrics to file instead of db')

    group_idb_tags = parser.getgroup('influxdb-tags', description='Additional tags for tests')
    group_idb_tags.addoption('--build-number', dest='build_number', help='CI build number')
    group_idb_tags.addoption('--build-name', dest='build_name', help='CI build name')


def pytest_configure(config: pytest.Config):
    """ Configure InfluxDB

    If idb_host variable exists init InfluxDB client and store it in global namespace
    """
    opts = config.option

    if opts.idb_host:
        try:
            client = IDBClient(host=opts.idb_host, port=opts.idb_port,
                               database=opts.idb_db, user=opts.idb_user, password=opts.idb_password,
                               dry_run=opts.influxdb_dry_run)

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

        # Get extra tags and fields from stash
        stash_values = item.stash.get(extra_values, None)
        if stash_values:
            extra_tags = stash_values.get(EXTRA_TAGS, None)
            extra_fields = stash_values.get(EXTRA_FIELDS, None)
        else:
            extra_tags = extra_fields = None

        try:
            data = PytestObject(item, reports, calls).to_dict(extra_tags=extra_tags, extra_fields=extra_fields)
            client.write_point(data, dry_run=item.config.option.influxdb_dry_run)
        except IDBClientException as e:
            logger.error(f'Cannot write point for test: {item.nodeid}.\nReason: {e}')
            if item.config.option.raise_influxdb_errors:
                raise e

