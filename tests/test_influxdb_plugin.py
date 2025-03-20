def test_help_message(testdir):
    result = testdir.runpytest(
        '--help',
    )
    result.stdout.fnmatch_lines([
        'InfluxDB Configuration:',
        '*--influxdb-host=IDB_HOST',
        '*InfluxDB host',
        '*--influxdb-port=IDB_PORT',
        '*InfluxDB port',
        '*--influxdb-user=IDB_USER',
        '*InfluxDB user',
        '*--influxdb-password=IDB_PASSWORD',
        '*InfluxDB password',
        '*--influxdb-db=IDB_DB*InfluxDB database name',
        '*--raise-influxdb-errors',
        '*Raise InfluxDB exceptions. Default: suppress exceptions',
        '*--influxdb-dry-run*Save metrics to file instead of db',
        '',
        'Additional tags for tests:',
        '*--build-number=BUILD_NUMBER',
        '*CI build number',
        '*--build-name=BUILD_NAME',
        '*CI build name',
    ])
