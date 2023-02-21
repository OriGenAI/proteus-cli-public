from ..default import DefaultConfig


class CnnPcaCaseConfig(DefaultConfig):
    """Configuration generator for the cases"""

    def step_1_litho_prop(self):
        """
        List all cases and its steps to generate the .GRDECL iterator

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """

        return (
            {
                "input": [
                    f'{case["root"]}/SIMULATION_{case["number"]}.GRDECL',
                ],
                "output": [f'{case["root"]}/litho.h5'],
                "preprocessing": "export_litho",
                "case": case["number"],
                "keep": True,
                "additional_info": {"get_mapping": self._get_mapping},
            }
            for case in self.cases
            if "BASE_CASE" not in str(case["root"])
        )
