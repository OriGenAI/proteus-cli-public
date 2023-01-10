from .defaultConfig import DefaultConfig


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
                    "input": [f'{first_case["root"]}' + f'/SIMULATION_{first_case["number"]}.DATA'],
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
                    "input": [f'{first_case["root"]}' + f'/SIMULATION_{first_case["number"]}.DATA'],
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
                    "input": [f'{f["source"].lower()}.dat' for f in _get_dat_files()],
                    "output": [f'{f["name"].lower()}.h5' for f in _get_dat_files()],
                    "preprocessing": "export_dat_properties",
                    "keep": True,
                    "additional_info": {"get_mapping": self._get_mapping},
                }
            ]
        )

    def step_4_actnum_prop(self):
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
                    "input": [(f'{first_case["root"]}/' f'SIMULATION_{first_case["number"]}.GRDECL')],
                    "output": ["actnum.h5"],
                    "preprocessing": "export_actnum",
                    "case": first_case["number"],
                    "keep": True,
                    "additional_info": {"get_mapping": self._get_mapping},
                }
            ]
        )


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


CommonConfigMapper = {"hm": HMCommonConfig, "cnn-pca": CnnPcaCommonConfig, "well-model": WellModelCommonConfig}
