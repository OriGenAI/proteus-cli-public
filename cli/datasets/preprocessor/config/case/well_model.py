import json
import os

from ..default import DefaultConfig

SMSPEC_WELL_KEYWORDS = ["WOPR", "WOPRH", "WWPR", "WWPRH", "WGPR", "WWIR", "WBHP", "WBHPH"]
SMSPEC_FIELD_KEYWORDS = ["FOPR", "FWPR", "FGPR", "FOPRH", "FWPRH", "FGPRH"]


class WellModelCaseConfig(DefaultConfig):
    """Configuration generator for the cases"""

    def step_1_grid_props(self):
        """
        List all cases and its steps to generate the .EGRID iterator

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """
        return (
            {
                "input": [f'{case["root"]}/SIMULATION_{case["number"]}.EGRID'],
                "output": [f'{case["root"]}/grid.h5'],
                "preprocessing": "export_egrid_properties",
                "split": case["group"],
                "case": case["number"],
                "keep": True,
            }
            for case in self.cases
        )

    def step_2_init_props(self):
        """
        List all cases and its steps to generate the .INIT iterator

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """
        init_keywords = []
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, "../../well_init_keywords.json")) as file:
            init_keywords = json.load(file)

        return (
            {
                "input": [
                    f'{case["root"]}/SIMULATION_{case["number"]}.INIT',
                    f'{case["root"]}/SIMULATION_{case["number"]}.EGRID',
                ],
                "output": list(
                    map(
                        lambda output: f'{case["root"]}/{output.get("filename")}',
                        init_keywords,
                    )
                ),
                "preprocessing": "export_well_init_properties",
                "split": case["group"],
                "case": case["number"],
                "keep": True,
                "additional_info": {"get_endpoint": self._get_endpoint},
            }
            for case in self.cases
        )

    def step_2_smry(self):
        """
        List all cases and its steps to generate the Summaries iterator

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """
        return (
            {
                "input": [
                    f'{case["root"]}/SIMULATION_{case["number"]}.SMSPEC',
                    f'{case["root"]}/SIMULATION_{case["number"]}.EGRID',
                    f'{case["root"]}/SIMULATION_{case["number"]}.X{str(case["finalStep"]).zfill(4)}',
                ]
                + [
                    f'{case["root"]}/SIMULATION_{case["number"]}.S{str(step).zfill(4)}'
                    for step in range(case["initialStep"], case["finalStep"])
                ],
                "output": [f'{case["root"]}/{k}.h5' for k in SMSPEC_WELL_KEYWORDS + SMSPEC_FIELD_KEYWORDS],
                "preprocessing": "export_smspec",
                "split": case["group"],
                "case": case["number"],
            }
            for case in self.cases
        )
