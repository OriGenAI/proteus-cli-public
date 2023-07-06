from preprocessing.common.csv_to_h5 import preprocess as preprocess_csv_to_h5

from cli.datasets.preprocessor.config import BaseConfig, CommonStepConfig
from cli.datasets.preprocessor.utils import RequiredFilePath


class FacilitiesCommonConfig(BaseConfig):
    """Configuration generator for the common files"""

    def step_1_network(self):
        """
        List the step to generate the network preprocessor

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """
        return (
            CommonStepConfig(
                input=(RequiredFilePath("network.csv", download_name="network"),),
                output=(RequiredFilePath("output.h5"),),
                preprocessing_fn=preprocess_csv_to_h5,
                keep=True,
                enabled=True,
            ),
        )
