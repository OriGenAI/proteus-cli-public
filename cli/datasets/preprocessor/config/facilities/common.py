from cli.datasets.preprocessor.config import BaseConfig, CommonStepConfig
from cli.utils.files import RequiredFilePath

from preprocessing.facilities.network import preprocess as preprocess_network


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
                input=(
                    RequiredFilePath("network.csv", download_name="network"),
                    RequiredFilePath("subsurface_mapping.csv", download_name="subsurface_mapping"),
                ),
                output=(
                    RequiredFilePath("network.json"),
                    # OptionalFilePath("network.svg")  # Not yet supported by the app
                ),
                preprocessing_fn=preprocess_network,
                keep=True,
                enabled=True,
            ),
        )
