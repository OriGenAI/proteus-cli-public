from cli.datasets.preprocessor.config import CaseStepConfig
from cli.datasets.preprocessor.config.cnn_pca import BaseCnnPcaCaseConfig
from cli.datasets.preprocessor.preprocess_functions import export_litho
from cli.utils.files import RequiredFilePath


class CnnPcaCaseConfig(BaseCnnPcaCaseConfig):
    """Configuration generator for the cases"""

    def step_1_lito_prop(self):

        if not self.litho_input:
            return tuple()

        return tuple(
            CaseStepConfig(
                input=(RequiredFilePath("*.GRDECL", download_name="litho_input"),),
                output=(RequiredFilePath("litho.h5")),
                preprocessing_fn=export_litho,
            )
            for case in self.cases
            if "BASE_CASE" not in str(case["root"])
        )
