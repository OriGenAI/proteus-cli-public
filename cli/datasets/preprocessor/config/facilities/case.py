from pathlib import Path

from cli.datasets.preprocessor.config import BaseConfig, CaseStepConfig
from cli.utils.files import RequiredFilePath
from preprocessing.facilities.flowline import preprocess as preprocess_flowline


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
                input=(RequiredFilePath("network.csv", download_name="network"),)
                + tuple(RequiredFilePath(input_path, download_name="flowlines") for input_path in group_conf["cases"]),
                output=(RequiredFilePath(group_conf["output_path"]),),
                preprocessing_fn=preprocess_flowline,
                root=str(
                    group_conf["root"]
                ),  # The only path that needs to be a string for internal susbstrings processing
                split=group_name,
                case=None,
                keep=True,
                enabled=True,
            )
            for group_name, group_conf in groups.items()
        )
