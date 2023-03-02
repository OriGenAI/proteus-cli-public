from cli.datasets.preprocessor.config.common.cnn_pca import CnnPcaCommonConfig
from cli.datasets.preprocessor.config.common.hm import HMCommonConfig
from cli.datasets.preprocessor.config.common.well_model import WellModelCommonConfig

CommonConfigMapper = {"hm": HMCommonConfig, "cnn-pca": CnnPcaCommonConfig, "well-model": WellModelCommonConfig}

__all__ = ["CommonConfigMapper", "HMCommonConfig", "WellModelCommonConfig", "CnnPcaCommonConfig"]
