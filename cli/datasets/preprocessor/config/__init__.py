from .defaultConfig import DefaultConfig

from .CaseConfig import CaseConfig
from .StepConfig import StepConfig
from .CommonConfig import CommonConfig

# Config object wrapping all properties
class Config(DefaultConfig):
  def step_1_cases_function(self):
    config = CaseConfig(cases=self.cases)
    result = config.return_iterator()

    return result
  
  def step_2_steps_function(self):
    config = StepConfig(cases=self.cases)
    result = config.return_iterator()

    return result

  def step_3_common_function(self):
    config = CommonConfig(cases=self.cases)
    result = config.return_iterator()

    return result



