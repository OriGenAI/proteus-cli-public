from ..default import DefaultConfig


class HMStepConfig(DefaultConfig):
    """Configuration generator for the steps"""

    """ Private methods """

    def _get_common_data(self):
        return self.common_data

    def _set_common_data(self, common_data):
        self.common_data = common_data

    def step_1_restart_file(self):
        """
        Return the restart file

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """

        return (
            {
                "input": [f'{case["root"]}/SIMULATION_{case["number"]}.X0000'],
                "output": [
                    f'{case["root"]}/X0000_pressure.h5',
                    f'{case["root"]}/X0000_swat.h5',
                ],
                "preprocessing": "export_x_file",
                "split": case["group"],
                "case": case["number"],
                "post_processing_info": {
                    "get_common_data": self._get_common_data,
                    "set_common_data": self._set_common_data,
                },
                "post_processing_function_name": "postprocess_common_file",
                "keep": True,
            }
            for case in self.cases
        )

    def step_2_x_files(self):
        """
        List all cases and its steps to generate the X files iterator

        Args: -

        Returns:
            iterator: the list of steps to preprocess
        """

        result = []

        def step_terms(case, step):
            return {
                "input": [f'{case["root"]}/' f'SIMULATION_{case["number"]}.X{str(step).zfill(4)}'],
                "output": [
                    f'{case["root"]}/X{str(step).zfill(4)}_pressure.h5',
                    f'{case["root"]}/X{str(step).zfill(4)}_swat.h5',
                ],
                "preprocessing": "export_x_file",
                "split": case["group"],
                "case": case["number"],
                "post_processing_info": {
                    "get_common_data": self._get_common_data,
                    "set_common_data": self._set_common_data,
                },
                "post_processing_function_name": "postprocess_common_file",
            }

        for case in self.cases:
            steps = [step_terms(case, step) for step in range(case["initialStep"], case["finalStep"])]
            result.extend(steps)

        return iter(result)
