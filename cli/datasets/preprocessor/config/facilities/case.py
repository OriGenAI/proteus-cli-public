from pathlib import Path

from preprocessing.facilities.flowline import preprocess as preprocess_flowline

from cli.datasets.preprocessor.config import BaseConfig, CaseStepConfig
from cli.utils.files import RequiredFilePath


class FacilitiesCaseConfig(BaseConfig):
    """Configuration generator for the case files"""

    def step_1_flowline(self):
        """
        Create a preprocesor for each case group

        Args: -

        Returns:
            iterator: the list of groups to preprocess
        """
        groups = {}
        for c in self.cases:
            group = c["group"]
            if group not in groups:
                groups[group] = {
                    "cases": [],
                    "output_path": Path(c["root"]).parents[0] / "flowline.h5",  # cases/{group}/flowline.h5
                    "root": Path(c["root"]).parents[2],  # cases/{group}/SIMULATION_{case}/../../..
                }

            # old_root = os.path.join(os.path.join(os.path.split(cases[0]["root"])[0], ".."), "..")
            input_path = Path(c["root"]) / "*.csv"  # cases/{group}/SIMULATION_{case}/*.csv
            groups[group]["cases"].append(input_path)

        return tuple(
            CaseStepConfig(
                input=(RequiredFilePath("network.csv"),)
                + tuple(RequiredFilePath(input_path) for input_path in group["cases"]),
                output=(RequiredFilePath(group["output_path"]),),
                preprocessing_fn=preprocess_flowline,
                root=str(group["root"]),  # The only path that needs to be a string for internal susbstrings processing
                split=group_name,
                case=None,
                keep=True,
                enabled=True,
            )
            for group_name, group in groups.items()
        )
