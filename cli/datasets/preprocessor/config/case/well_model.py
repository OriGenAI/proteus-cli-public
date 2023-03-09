import json
import os

from ..default import DefaultConfig
from ...utils import RequiredFilePath

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
                "input": [f'{case["root"]}/*.EGRID'],
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
                    RequiredFilePath(f'{case["root"]}/*.INIT', download_name="init"),
                    RequiredFilePath(f'{case["root"]}/*.EGRID', download_name="grid"),
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

    def step_3_smspec(self):
        """
        List all cases and its steps to generate the Summaries iterator

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """
        return (
            {
                "input": [
                    RequiredFilePath(f'{case["root"]}/*.SMSPEC', download_name="smspec"),
                ]
                + [
                    RequiredFilePath(f'{case["root"]}/*.S{str(step).zfill(4)}', download_name="s")
                    for step in range(case["initialStep"] + 1, case["finalStep"] + 1)
                ],
                "output": [f'{case["root"]}/{k}.h5' for k in SMSPEC_WELL_KEYWORDS + SMSPEC_FIELD_KEYWORDS],
                "preprocessing": "export_smspec",
                "split": case["group"],
                "case": case["number"],
            }
            for case in self.cases
        )
