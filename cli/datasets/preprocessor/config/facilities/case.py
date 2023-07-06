from preprocessing.common.csv_to_h5 import preprocess as preprocess_csv_to_h5

from cli.datasets.preprocessor.config import BaseConfig, CaseStepConfig
from cli.datasets.preprocessor.utils import RequiredFilePath


class FacilitiesCaseConfig(BaseConfig):
    """Configuration generator for the case files"""

    def step_1_flowline(self):
        """
        List the steps to generate the flowline preprocessor

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """
        return tuple(
            CaseStepConfig(
                input=(RequiredFilePath("*.csv", download_name="flowline"),),
                output=(RequiredFilePath("output.h5"),),
                preprocessing_fn=preprocess_csv_to_h5,
                root=case["root"],
                split=case["group"],
                case=case["number"],
                keep=True,
                enabled=True
            )
            for case in self.cases
        )
