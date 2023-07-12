from preprocessing.facilities.network import preprocess as preprocess_network

from cli.datasets.preprocessor.config import BaseConfig, CommonStepConfig
from cli.utils.files import RequiredFilePath


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
                output=(RequiredFilePath("network.json"),),
                preprocessing_fn=preprocess_network,
                keep=True,
                enabled=True,
            ),
        )
