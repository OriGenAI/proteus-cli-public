from cli.datasets.preprocessor.config.step.cnn_pca import CnnPcaStepConfig
from cli.datasets.preprocessor.config.step.hm import HMStepConfig
from cli.datasets.preprocessor.config.step.well_model import WellModelStepConfig

StepConfigMapper = {"hm": HMStepConfig, "cnn-pca": CnnPcaStepConfig, "well-model": WellModelStepConfig}

__all__ = ["StepConfigMapper", "HMStepConfig", "WellModelStepConfig", "CnnPcaStepConfig"]
