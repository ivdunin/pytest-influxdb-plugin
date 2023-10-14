import logging
from typing import Dict, Tuple, List

from _pytest import reports, runner
from _pytest.nodes import Item

logger = logging.getLogger(__name__)

EMPTY_VALUE = 'N/A'
SETUP = 'setup'
CALL = 'call'
TEARDOWN = 'teardown'
STAGES = [SETUP, CALL, TEARDOWN]


class PytestObject:
    def __init__(self, item: Item, report: Dict[str, reports.TestReport], call: Dict[str, runner.CallInfo]):
        self._item: Item = item
        self._reports: Dict[str, reports.TestReport] = report
        self._calls: Dict[str, runner.CallInfo] = call

    @property
    def build_name(self):
        return self._item.config.getoption('build_name', EMPTY_VALUE)

    @property
    def build_number(self):
        return self._item.config.getoption('build_number', 0)

    @property
    def parent_build_name(self):
        return self._item.config.getoption('parent_build_name', EMPTY_VALUE)

    @property
    def parent_build_number(self):
        return self._item.config.getoption('parent_build_number', 0)

    def _get_test_markers(self) -> str:
        """ Get sorted comma string of markers assigned to test """
        markers = set()
        for mark in self._item.parent.own_markers + self._item.own_markers:
            if mark.name not in ('filterwarnings', 'parametrize', 'skip', 'skipif', 'usefixtures', 'xfail'):
                markers.add(mark.name)

        return ','.join(sorted(markers))

    def _is_xfail(self):
        """ Check if test xfail """
        for mark in self._item.parent.own_markers + self._item.own_markers:
            if mark.name == 'xfail':
                return True
        return False

    def _get_duration(self, stage: str) -> float:
        """ Get stage duration """
        if stage in self._reports:
            return float(self._reports[stage].duration)
        else:
            return 0.0

    def _get_exceptions(self):
        """ Get test exceptions as string """
        exceptions = []
        for stage in STAGES:
            if stage in self._calls and self._calls[stage].excinfo:
                call = self._calls[stage]
                text = '; '.join(str(call.excinfo.value).split('\n'))
                exceptions.append(f'{stage} > {call.excinfo.typename}: {text}')

        return '\n'.join(exceptions)

    def _get_failed_stages(self):
        """ Get failed stages """
        failed_stages = []
        for stage in STAGES:
            if stage in self._reports and (self._reports[stage].failed or
                                           (self._reports[stage].skipped and self._is_xfail())):
                failed_stages.append(stage)

        return ','.join(failed_stages)

    def _get_test_params(self):
        """ Get test params as dash string """
        if hasattr(self._item, 'callspec'):
            if self._item.callspec.id:
                return self._item.callspec.id
            else:
                params = [str(p) for p in self._item.callspec.params.values()]
                return '-'.join(params)
        else:
            return ''

    def _get_test_status(self) -> Tuple[str, str]:
        """ Return test statuses for pytest and allure """
        if self._reports[SETUP].failed:
            if self._calls[SETUP].excinfo.typename == 'AssertionError':
                return 'error', 'failed'
            else:
                return 'error', 'broken'
        elif CALL not in self._reports:
            if not self._is_xfail():
                return 'skipped', 'skipped'
            else:
                return 'xfailed', 'skipped'
        elif CALL in self._reports:
            if self._reports[CALL].failed:
                if self._calls[CALL].excinfo.typename == 'AssertionError':
                    return 'failed', 'failed'
                else:
                    return 'failed', 'broken'
            if self._reports[CALL].passed:
                if self._is_xfail():
                    return 'xpassed', 'passed'
                else:
                    # If test passed, but teardown failed, allure marked such tests as failed/broken
                    if self._reports[TEARDOWN].failed:
                        if self._calls[TEARDOWN].excinfo.typename == 'AssertionError':
                            return 'passed', 'failed'
                        else:
                            return 'passed', 'broken'
                    else:
                        return 'passed', 'passed'
            if self._reports[CALL].skipped:
                return 'xfailed', 'skipped'

        logger.error(f'Unknown status for test: {self._item.originalname} ({self._item.nodeid})')
        return 'unknown', 'unknown'

    def to_dict(self) -> List[dict]:
        """ Get metrics for influxdb """
        def validate_tags(_tags: dict):
            for k, v in _tags.items():
                if not v.strip():
                    _tags[k] = EMPTY_VALUE

        pytest_status, allure_status = self._get_test_status()
        duration_setup = self._get_duration(SETUP)
        duration_call = self._get_duration(CALL)
        duration_teardown = self._get_duration(TEARDOWN)

        tags = {
            'test': self._item.originalname,
            'status': pytest_status,
            'allure_status': allure_status,
            'failed_stage': self._get_failed_stages(),
            'markers': self._get_test_markers(),
            'build_number': self.build_number,
            'build_name': self.build_name,
            'parent_build_name': self.parent_build_name,
            'parent_build_number': self.parent_build_number
        }

        validate_tags(tags)

        fields = {
            'duration_setup': duration_setup,
            'duration_call': duration_call,
            'duration_teardown': duration_teardown,
            'duration_total': duration_setup + duration_call + duration_teardown,
            'exception': self._get_exceptions(),
            'nodeid': self._item.nodeid,
            'params': self._get_test_params(),
        }

        json_body = [
            {
                "measurement": 'test_results',
                "tags": tags,
                "fields": fields
            }
        ]

        return json_body
