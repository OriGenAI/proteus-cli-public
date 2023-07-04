from cli.datasets.preprocessor.config import CaseStepConfig
from cli.datasets.preprocessor.config.cnn_pca import BaseCnnPcaCaseConfig
from cli.datasets.preprocessor.preprocess_functions import export_litho
from cli.datasets.preprocessor.utils import RequiredFilePath


class CnnPcaCaseConfig(BaseCnnPcaCaseConfig):
    """Configuration generator for the cases"""


    # def step_1_litho_prop(self):
    #     """
    #     List all cases and its steps to generate the .GRDECL iterator
    #
    #     Args: -
    #
    #     Returns:
    #         iterator: the list of steps to preprocess
    #     """
    #     mapping = [*filter(lambda x: x["name"] == "LITHO_INPUT", self._get_mapping())]
    #     return (
    #         {
    #             "input": [
    #                 f'{case["root"]}/SIMULATION_{case["number"]}.GRDECL',
    #             ],
    #             "output": [f'{case["root"]}/litho.h5'],
    #             "preprocessing": "export_litho",
    #             "case": case["number"],
    #             "keep": True,
    #             "additional_info": {"get_mapping": self._get_mapping},
    #         }
    #         for case in self.cases
    #         if len(mapping) > 0 and "BASE_CASE" not in str(case["root"])
    #     )

    def step_1_lito_prop(self):

        if not self.litho_input:
            return tuple()

        return tuple(
            CaseStepConfig(
                input=(
                    RequiredFilePath('*.GRDECL', download_name='litho_input'),
                ),
                output=(
                    RequiredFilePath('litho.h5')
                ),
                preprocessing_fn=export_litho
            )
            for case in self.cases
            if "BASE_CASE" not in str(case["root"])
        )
