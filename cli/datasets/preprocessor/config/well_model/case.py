import json
import os

from cli.datasets.preprocessor.config import BaseConfig, CaseStepConfig
from cli.datasets.preprocessor.config.well_model import SMSPEC_WELL_KEYWORDS, SMSPEC_FIELD_KEYWORDS
from cli.datasets.preprocessor.preprocess_functions import (
    export_egrid_properties,
    export_well_init_properties,
    export_smspec,
)
from cli.utils.files import RequiredFilePath, OptionalFilePath


class WellModelCaseConfig(BaseConfig):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        dir_path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(dir_path, "../../well_init_keywords.json")) as file:
            self.init_keywords = json.load(file)

    def step_1_grid_props(self):

        return tuple(
            CaseStepConfig(
                input=(
                    RequiredFilePath(
                        "*.EGRID", download_name="egrid", replace_with=RequiredFilePath("*.DATA", download_name="data")
                    ),
                ),
                output=(RequiredFilePath("grid.h5"),),
                root=case["root"],
                preprocessing_fn=export_egrid_properties,
                split=case["group"],
                case=case["number"],
                keep=False,
                enabled=True,
            )
            for case in self.cases
        )

    def step_2_init_props(self):

        return tuple(
            CaseStepConfig(
                input=(
                    RequiredFilePath("*.INIT", download_name="init"),
                    RequiredFilePath("*.EGRID", download_name="grid"),
                ),
                output=tuple(RequiredFilePath(output.get("filename")) for output in self.init_keywords),
                root=case["root"],
                preprocessing_fn=export_well_init_properties,
                split=case["group"],
                case=case["number"],
                keep=False,
                enabled=True,
            )
            for case in self.cases
        )

    def step_3_smspec(self):

        return tuple(
            CaseStepConfig(
                input=(RequiredFilePath("*.SMSPEC", download_name="smspec"),)
                + tuple(
                    RequiredFilePath(f"*.S{str(step).zfill(4)}", download_name="s")
                    for step in range(case["initialStep"] + 1, case["finalStep"] + 1)
                ),
                output=tuple(OptionalFilePath(f"{k}.h5") for k in SMSPEC_WELL_KEYWORDS + SMSPEC_FIELD_KEYWORDS),
                root=case["root"],
                preprocessing_fn=export_smspec,
                split=case["group"],
                keep=False,
                case=case["number"],
            )
            for case in self.cases
        )
