import os
from collections import defaultdict

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
        groups = defaultdict(list)
        for c in self.cases:
            groups[c["group"]].append(c)

        return tuple(
            CaseStepConfig(
                input=tuple(RequiredFilePath(f"{os.path.split(c['root'])[1]}/*.csv") for c in cases),
                output=(RequiredFilePath("flowline.h5"),),
                preprocessing_fn=preprocess_flowline,
                root=os.path.split(cases[0]["root"])[0],  # "cases/{group}"
                split=group,
                case=None,
                keep=True,
                enabled=True,
            )
            for group, cases in groups.items()
        )
