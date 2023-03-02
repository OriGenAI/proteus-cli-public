from .cnn_pca import CnnPcaCaseConfig
from .hm import HMCaseConfig
from .well_model import WellModelCaseConfig


CaseConfigMapper = {
    "hm": HMCaseConfig,
    "cnn-pca": CnnPcaCaseConfig,
    "well-model": WellModelCaseConfig,
}

__all__ = ["CaseConfigMapper", "HMCaseConfig", "WellModelCaseConfig", "CnnPcaCaseConfig"]
