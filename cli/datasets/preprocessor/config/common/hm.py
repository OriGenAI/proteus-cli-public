from ..default import DefaultConfig


class HMCommonConfig(DefaultConfig):
    """Configuration generator for the common files"""

    def step_1_common(self):
        """
        Generate the common properties iterator

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """
        return iter(
            [
                {
                    "input": [],
                    "output": ["common.p"],
                    "preprocessing": "noop",
                }
            ]
        )

    def step_2_metadata(self):
        """
        List all cases and its steps to generate the Metadata iterator

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """
        first_case = self.cases[0]
        return iter(
            [
                {
                    "input": [],
                    "output": ["ecl_deck.p"],
                    "preprocessing": "export_deck",
                    "split": first_case["group"],
                    "case": first_case["number"],
                    "additional_info": {
                        "group": first_case["group"],
                        "number": first_case["number"],
                    },
                }
            ]
        )

    def step_3_runspec(self):
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
                    "input": [f'{first_case["root"]}' + f'/SIMULATION_{first_case["number"]}.DATA'],
                    "output": ["runspec.p"],
                    "preprocessing": "export_runspec",
                    "split": first_case["group"],
                    "case": first_case["number"],
                    "additional_info": {"set_endpoint": self._set_endpoint},
                }
            ]
        )
