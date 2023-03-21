from ..default import DefaultConfig
from ...utils import RequiredFilePath


class CnnPcaCommonConfig(DefaultConfig):
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
                    "input": [RequiredFilePath(f'{str(first_case["root"]).rstrip("/")}/*.DATA', download_name="data")],
                    "output": ["runspec.p"],
                    "preprocessing": "export_runspec",
                    "case": first_case["number"],
                    "keep": True,
                    "additional_info": {"set_endpoint": self._set_endpoint},
                }
            ]
        )

    def step_2_wellspec(self):
        """
        List all cases and its steps to generate the Summaries iterator

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """
        first_case = self.cases[0]
        return iter(
            [
                {
                    "input": [RequiredFilePath(f'{str(first_case["root"]).rstrip("/")}/*.DATA', download_name="data")],
                    "output": ["well_spec.p"],
                    "preprocessing": "export_wellspec",
                    "keep": True,
                    "case": first_case["number"],
                }
            ]
        )

    def step_3_dat_files(self):
        """
        Generate .dat iterator

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """

        def _get_dat_files():
            return filter(
                lambda f: f["name"].lower() not in ["litho", "actnum"],
                self._get_mapping(),
            )

        return iter(
            [
                {
                    "input": [f'{f.get("source")}.dat' for f in _get_dat_files()],
                    "output": [f'{f["name"].lower()}.h5' for f in _get_dat_files()],
                    "preprocessing": "export_dat_properties",
                    "keep": True,
                    "additional_info": {"get_mapping": self._get_mapping},
                }
            ]
        )

    # def step_4_actnum_prop(self):
    #     """
    #     List all cases and its steps to generate the .DATA iterator
    #
    #     Args: -
    #
    #     Returns:
    #         iterator: the list of steps to preprocess
    #     """
    #     first_case = self.cases[0]
    #     return iter(
    #         [
    #             {
    #                 "input": [
    #                     RequiredFilePath(
    #                         f'{str(first_case["root"]).rstrip("/")}/' f"*ACTNUM.GRDECL", download_name="actnum"
    #                     )
    #                 ],
    #                 "output": ["actnum.h5"],
    #                 "preprocessing": "export_actnum",
    #                 "case": first_case["number"],
    #                 "keep": True,
    #                 "additional_info": {"get_mapping": self._get_mapping},
    #             }
    #         ]
    #     )
