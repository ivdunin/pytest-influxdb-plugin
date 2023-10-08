import pytest


@pytest.mark.parametrize(
    'influxdb_host, expected_type', [
        pytest.param('', 'type(None)', id='InfluxDB host not defined')
    ]
)
def test_fixture_idb_client(testdir, influxdb_host, expected_type):
    """ Make sure that pytest correctly initialize InfluxDB fixture """

    testdir.makepyfile(f"""
        from pytest_influxdb_plugin.idb_client import IDBClient

        def test_fxt(idb_client):
            assert isinstance(idb_client, {expected_type}), 'Incorrect type'
    """)

    result = testdir.runpytest(
        f'--influx-host={influxdb_host}',
        '-v'
    )

    result.stdout.fnmatch_lines([
        '*::test_fxt PASSED*',
    ])

    assert result.ret == 0


def test_help_message(testdir):
    result = testdir.runpytest(
        '--help',
    )
    result.stdout.fnmatch_lines([
        'influxdb-plugin:',
        '*--influx-host=IDB_HOST',
        '*InfluxDB host',
        '*--influx-port=IDB_PORT',
        '*InfluxDB port',
        '*--influx-user=IDB_USER',
        '*InfluxDB user',
        '*--influx-password=IDB_PASSWORD',
        '*InfluxDB password',
        '*--influx-db=IDB_DB*InfluxDB database name',
        '*--use-original-name*Use original test name instead of node name.',
        '',
        'influxdb-tags:',
        '*--build-number=BUILD_NUMBER',
        '*CI build number',
        '*--build-name=BUILD_NAME',
        '*CI build name',
        '*--parent-build-number=PARENT_BUILD_NUMBER',
        '*CI parent build number',
        '*--parent-build-name=PARENT_BUILD_NAME',
        '*CI parent build name'
    ])
