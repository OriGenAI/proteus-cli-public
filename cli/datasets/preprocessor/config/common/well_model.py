from ..default import DefaultConfig


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
                    "input": [f'{first_case["root"]}/SIMULATION_{first_case["number"]}.DATA'],
                    "output": ["runspec.p"],
                    "preprocessing": "export_runspec",
                    "split": first_case["group"],
                    "case": first_case["number"],
                    "additional_info": {"set_endpoint": self._set_endpoint},
                }
            ]
        )
