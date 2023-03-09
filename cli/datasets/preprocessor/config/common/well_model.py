from ..default import DefaultConfig
from ...utils import RequiredFilePath


class WellModelCommonConfig(DefaultConfig):
    """Configuration generator for the common files"""

    def step_1_runspec(self):
        """
        List all cases and its steps to generate the .DATA iterator

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """
        first_case = self.cases[0]
        return iter(
            [
                {
                    "input": [
                        RequiredFilePath(f'{first_case["root"]}/*.DATA', download_name="data"),
                        # Required to extract well names
                        RequiredFilePath(f'{first_case["root"]}/*.SMSPEC', download_name="smspec"),
                        RequiredFilePath(f'{first_case["root"]}/*.EGRID', download_name="egrid"),
                        RequiredFilePath(
                            f'{first_case["root"]}/*.S{str(first_case["finalStep"]).zfill(4)}', download_name="s"
                        ),
                        RequiredFilePath(f'{first_case["root"]}/*.INIT', download_name="init"),
                    ],
                    "continue_if_missing": [".inc", ".grdecl"],
                    "output": ["runspec.p"],
                    "preprocessing": "export_runspec",
                    "split": first_case["group"],
                    "case": first_case["number"],
                    "additional_info": {"set_endpoint": self._set_endpoint},
                }
            ]
        )
