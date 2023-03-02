from .case import CaseConfigMapper
from .common import CommonConfigMapper
from .default import DefaultConfig
from .step import StepConfigMapper


# Config object wrapping all properties
class Config(DefaultConfig):
    def __init__(self, workflow="hm", **kwargs):
        super().__init__(**kwargs)
        self._workflow = workflow

    def step_1_common_function(self):
        ConfigCls = CommonConfigMapper[self._workflow]
        config = ConfigCls(cases=self.cases)
        result = config.return_iterator()

        return result

    def step_2_cases_function(self):
        ConfigCls = CaseConfigMapper[self._workflow]
        config = ConfigCls(cases=self.cases)
        result = config.return_iterator()

        return result

    def step_3_steps_function(self):
        ConfigCls = StepConfigMapper[self._workflow]
        config = ConfigCls(cases=self.cases)
        result = config.return_iterator()

        return result
