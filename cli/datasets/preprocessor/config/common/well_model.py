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
                        RequiredFilePath(f'{first_case["root"]}/SIMULATION_{first_case["number"]}.DATA'),
                        # Required to extract well names
                        RequiredFilePath(f'{first_case["root"]}/SIMULATION_{first_case["number"]}.SMSPEC'),
                        RequiredFilePath(
                            f'{first_case["root"]}/SIMULATION_'
                            f'{first_case["number"]}.S{str(first_case["initialStep"]).zfill(4)}'
                        ),
                    ],
                    "output": ["runspec.p"],
                    "preprocessing": "export_runspec",
                    "split": first_case["group"],
                    "case": first_case["number"],
                    "additional_info": {"set_endpoint": self._set_endpoint},
                }
            ]
        )
