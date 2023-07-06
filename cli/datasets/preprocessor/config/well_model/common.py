from cli.datasets.preprocessor.config import BaseConfig, CommonStepConfig
from cli.datasets.preprocessor.preprocess_functions import export_runspec
from cli.utils.files import RequiredFilePath


class WellModelCommonConfig(BaseConfig):
    """Configuration generator for the common files"""

    def step_1_runspec(self):
        """
        List all cases and its steps to generate the .DATA iterator

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """
        first_case = self.cases[0]

        return (
            CommonStepConfig(
                input=(
                    RequiredFilePath(f'{first_case["root"]}/*.DATA', download_name="data"),
                    # Required to extract well names
                    RequiredFilePath(f'{first_case["root"]}/*.SMSPEC', download_name="smspec"),
                    RequiredFilePath(f'{first_case["root"]}/*.EGRID', download_name="egrid"),
                    RequiredFilePath(
                        f'{first_case["root"]}/*.S{str(first_case["finalStep"]).zfill(4)}', download_name="s"
                    ),
                    RequiredFilePath(f'{first_case["root"]}/*.INIT', download_name="init"),
                ),
                output=(RequiredFilePath("runspec.p"),),
                preprocessing_fn=export_runspec,
                keep=True,
                enabled=True,
            ),
        )
